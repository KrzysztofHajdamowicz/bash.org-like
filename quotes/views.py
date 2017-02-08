# -*- coding: UTF-8 -*-
import json
from django.http import *
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.conf import settings
from django.utils import timezone
from .models import Quote
from .forms import AddQuoteForm


# Create your views here.


def login_user(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/manage/')
    else:
        logout(request)
        username = password = ''
        if request.POST:
            username = request.POST['username']
            password = request.POST['password']

            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/manage/')
    print(settings.SITE_NAME)
    return render(request, 'quotes/login_form.html', {'site_name': settings.SITE_NAME, 'context': 'login_user'})


def index_view(request):
    return render(request, 'quotes/welcome.html', {'site_name': settings.SITE_NAME, 'context': 'index_view'})


def accepted_list(request):
    quotes = Quote.objects.all().filter(status=3).order_by('-id')

    # https://docs.djangoproject.com/pl/1.10/topics/pagination/
    paginator = Paginator(quotes, 10)
    page = request.GET.get('page')
    try:
        quotes = paginator.page(page)
    except PageNotAnInteger:
        quotes = paginator.page(1)
    except EmptyPage:
        quotes = paginator.page(paginator.num_pages)

    return render(request,
                  'quotes/quotes_list.html',
                  {'quotes': quotes, 'site_name': settings.SITE_NAME, 'context': 'accepted_list'})


def best_list(request):
    quotes = Quote.objects.all().filter(status=3).extra(select={'karma': 'votes_up - votes_down'}).order_by('-karma', '-id')

    # https://docs.djangoproject.com/pl/1.10/topics/pagination/
    paginator = Paginator(quotes, 10)
    page = request.GET.get('page')
    try:
        quotes = paginator.page(page)
    except PageNotAnInteger:
        quotes = paginator.page(1)
    except EmptyPage:
        quotes = paginator.page(paginator.num_pages)

    return render(request,
                  'quotes/quotes_list.html',
                  {'quotes': quotes, 'site_name': settings.SITE_NAME, 'context': 'best_list'})


def trash_list(request):
    quotes = Quote.objects.all().filter(status=2).order_by('-id')[:10]
    return render(request, 'quotes/quotes_list.html', {'quotes': quotes, 'site_name': settings.SITE_NAME, 'context': 'trash_list'})


def quote_view(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    return render(request, 'quotes/quotes_view.html', {'quote': quote, 'site_name': settings.SITE_NAME, 'context': 'accepted_list'})


def quote_add(request):
    if request.method == "POST":
        form = AddQuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.save()
            return render(request, 'quotes/quote_added.html', {'site_name': settings.SITE_NAME, 'context': 'quote_add'})
    else:
        form = AddQuoteForm()
        return render(request, 'quotes/quote_add.html', {'form': form, 'site_name': settings.SITE_NAME, 'context': 'quote_add'})


@login_required(login_url='/login/')
def quote_manage(request):
    quotes = Quote.objects.all().filter(status=1).order_by('-id')[:10]
    return render(request, 'quotes/quotes_manage.html', {'quotes': quotes, 'site_name': settings.SITE_NAME, 'context': 'quote_manage'})


@login_required(login_url='/login/')
def quote_accept(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.status = 3
    quote.acceptant = request.user
    quote.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required(login_url='/login/')
def quote_reject(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.status = 2
    quote.acceptant = request.user
    quote.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required(login_url='/login/')
def quote_delete(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def quote_vote_up(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.votes_up += 1
    quote.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def quote_vote_down(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.votes_down += 1
    quote.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def quote_ajax(request):
    if not request.is_ajax():
        pass  # You can handle with it
    quote = Quote.objects.get(pk=request.GET['quote_id'])
    quote.votes_up += 1
    quote.save()
    return HttpResponse(
        json.dumps({"current_votes": quote.votes_up - quote.votes_down}),
        content_type="application/json"
    )
