from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.conf import settings

from .forms import AddQuoteForm
from .models import Quote


def login_user(request):
    if request.user.is_authenticated:
        return redirect("quote_manage")
    logout(request)
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("quote_manage")
    return render(request, "quotes/login_form.html", {"site_name": settings.SITE_NAME, "context": "login_user"})


def index_view(request):
    return render(request, "quotes/welcome.html", {"site_name": settings.SITE_NAME, "context": "index_view"})


def accepted_list(request):
    quotes = Quote.objects.filter(status=Quote.Status.APPROVED).order_by("-id")

    paginator = Paginator(quotes, 10)
    page = request.GET.get("page")
    try:
        quotes = paginator.page(page)
    except PageNotAnInteger:
        quotes = paginator.page(1)
    except EmptyPage:
        quotes = paginator.page(paginator.num_pages)

    return render(
        request,
        "quotes/quotes_list.html",
        {"quotes": quotes, "site_name": settings.SITE_NAME, "context": "accepted_list"},
    )


def best_list(request):
    quotes = (
        Quote.objects.filter(status=Quote.Status.APPROVED)
        .annotate(karma=F("votes_up") - F("votes_down"))
        .order_by("-karma", "-id")
    )

    paginator = Paginator(quotes, 10)
    page = request.GET.get("page")
    try:
        quotes = paginator.page(page)
    except PageNotAnInteger:
        quotes = paginator.page(1)
    except EmptyPage:
        quotes = paginator.page(paginator.num_pages)

    return render(
        request, "quotes/quotes_list.html", {"quotes": quotes, "site_name": settings.SITE_NAME, "context": "best_list"}
    )


def trash_list(request):
    quotes = Quote.objects.filter(status=Quote.Status.REJECTED).order_by("-id")[:10]
    return render(
        request,
        "quotes/quotes_list.html",
        {"quotes": quotes, "site_name": settings.SITE_NAME, "context": "trash_list"},
    )


def quote_view(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    return render(
        request, "quotes/quotes_view.html", {"quote": quote, "site_name": settings.SITE_NAME, "context": "quote_view"}
    )


def quote_add(request):
    if request.method == "POST":
        form = AddQuoteForm(request.POST)
        if form.is_valid():
            form.save()
            return render(
                request, "quotes/quote_added.html", {"site_name": settings.SITE_NAME, "context": "quote_add"}
            )
    else:
        form = AddQuoteForm()
    return render(
        request, "quotes/quote_add.html", {"form": form, "site_name": settings.SITE_NAME, "context": "quote_add"}
    )


@login_required(login_url="/login/")
def quote_manage(request):
    quotes = Quote.objects.filter(status=Quote.Status.PENDING).order_by("-id")[:10]
    return render(
        request,
        "quotes/quotes_manage.html",
        {"quotes": quotes, "site_name": settings.SITE_NAME, "context": "quote_manage"},
    )


@login_required(login_url="/login/")
@require_POST
def quote_accept(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.status = Quote.Status.APPROVED
    quote.acceptant = request.user
    quote.save()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required(login_url="/login/")
@require_POST
def quote_reject(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.status = Quote.Status.REJECTED
    quote.acceptant = request.user
    quote.save()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required(login_url="/login/")
@require_POST
def quote_delete(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.delete()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@require_POST
def quote_vote_up(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.votes_up += 1
    quote.save()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@require_POST
def quote_vote_down(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.votes_down += 1
    quote.save()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@require_POST
def quote_ajax(request):
    quote_id = request.POST.get("quote_id")
    if not quote_id:
        return JsonResponse({"error": "Missing quote_id"}, status=400)
    try:
        quote = Quote.objects.get(pk=quote_id)
    except Quote.DoesNotExist:
        return JsonResponse({"error": "Quote not found"}, status=404)
    quote.votes_up += 1
    quote.save()
    return JsonResponse({"current_votes": quote.votes_up - quote.votes_down})
