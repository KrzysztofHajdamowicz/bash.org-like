from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import AddQuoteForm
from .models import Quote


def get_safe_redirect_url(request, fallback="/"):
    referrer = request.META.get("HTTP_REFERER")
    if not referrer:
        return fallback
    allowed_hosts = set(settings.ALLOWED_HOSTS)
    if "*" in allowed_hosts:
        # In dev mode ALLOWED_HOSTS=["*"], but url_has_allowed_host_and_scheme
        # treats "*" as a literal hostname. Fall back to the request host.
        allowed_hosts = {request.get_host()}
    if url_has_allowed_host_and_scheme(
        referrer,
        allowed_hosts=allowed_hosts,
        require_https=request.is_secure(),
    ):
        return referrer
    return fallback


def _paginate(queryset, request, per_page=10):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get("page")
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def login_user(request):
    if request.user.is_authenticated:
        return redirect("quote_manage")
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("quote_manage")
    return render(request, "quotes/login_form.html", {"active_nav": "login_user"})


@login_required(login_url="/login/")
def logout_user(request):
    logout(request)
    return redirect("index_view")


def index_view(request):
    return render(request, "quotes/welcome.html", {"active_nav": "index_view"})


def accepted_list(request):
    quotes = Quote.objects.filter(status=Quote.Status.APPROVED).order_by("-id")
    quotes = _paginate(quotes, request)
    return render(request, "quotes/quotes_list.html", {"quotes": quotes, "active_nav": "accepted_list"})


def best_list(request):
    quotes = (
        Quote.objects.filter(status=Quote.Status.APPROVED)
        .annotate(karma=F("votes_up") - F("votes_down"))
        .order_by("-karma", "-id")
    )
    quotes = _paginate(quotes, request)
    return render(request, "quotes/quotes_list.html", {"quotes": quotes, "active_nav": "best_list"})


def trash_list(request):
    quotes = Quote.objects.filter(status=Quote.Status.REJECTED).order_by("-id")
    quotes = _paginate(quotes, request)
    return render(request, "quotes/quotes_list.html", {"quotes": quotes, "active_nav": "trash_list"})


def quote_view(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    return render(request, "quotes/quotes_view.html", {"quote": quote, "active_nav": "quote_view"})


def quote_add(request):
    if request.method == "POST":
        form = AddQuoteForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, "quotes/quote_added.html", {"active_nav": "quote_add"})
    else:
        form = AddQuoteForm()
    return render(request, "quotes/quote_add.html", {"form": form, "active_nav": "quote_add"})


@login_required(login_url="/login/")
def quote_manage(request):
    quotes = Quote.objects.filter(status=Quote.Status.PENDING).order_by("-id")
    quotes = _paginate(quotes, request)
    return render(request, "quotes/quotes_manage.html", {"quotes": quotes, "active_nav": "quote_manage"})


@login_required(login_url="/login/")
@require_POST
def quote_accept(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.status = Quote.Status.APPROVED
    quote.acceptant = request.user
    quote.save(update_fields=["status", "acceptant"])
    return HttpResponseRedirect(get_safe_redirect_url(request))


@login_required(login_url="/login/")
@require_POST
def quote_reject(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.status = Quote.Status.REJECTED
    quote.acceptant = request.user
    quote.save(update_fields=["status", "acceptant"])
    return HttpResponseRedirect(get_safe_redirect_url(request))


@login_required(login_url="/login/")
@require_POST
def quote_delete(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.delete()
    return HttpResponseRedirect(get_safe_redirect_url(request))


@require_POST
def quote_vote_up(request, quote_id):
    get_object_or_404(Quote, pk=quote_id)
    Quote.objects.filter(pk=quote_id).update(votes_up=F("votes_up") + 1)
    return HttpResponseRedirect(get_safe_redirect_url(request))


@require_POST
def quote_vote_down(request, quote_id):
    get_object_or_404(Quote, pk=quote_id)
    Quote.objects.filter(pk=quote_id).update(votes_down=F("votes_down") + 1)
    return HttpResponseRedirect(get_safe_redirect_url(request))


@require_POST
def quote_ajax(request):
    quote_id = request.POST.get("quote_id")
    if not quote_id:
        return JsonResponse({"error": "Missing quote_id"}, status=400)
    try:
        quote = Quote.objects.get(pk=quote_id)
    except Quote.DoesNotExist:
        return JsonResponse({"error": "Quote not found"}, status=404)
    Quote.objects.filter(pk=quote.pk).update(votes_up=F("votes_up") + 1)
    quote.refresh_from_db()
    return JsonResponse({"current_votes": quote.votes_up - quote.votes_down})
