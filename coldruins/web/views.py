from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.core.urlresolvers import reverse as url_reverse
from django.db import transaction, IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import ensure_csrf_cookie
import facebook

import json

from coldruins.web.decorators import *
from coldruins.web.models import User, UserMeta
from coldruins.web.fbgraph import *

@ensure_csrf_cookie
def home(request):
  return HttpResponse(
      open('coldruins/web/static/index.html', 'rt').read())

def locations(request):
  token = 'BAACEdEose0cBAE5X5Uq47awMD9keThPrZCZBQsWUzHvNuNgmY43EslangMfcuZAWdPZCrrVoZBKl9JUCQ9Yigt4HntyDzXuVx4AazxftqpLOZB1HY6SC11EM0xl7CXmZCusN0hAFEM5xMCpZBmCttKiO6HBaBuZBtPZC6uaRjjQPARRDQ7f0L3EcPc7EDnYfzqONp7ZA9umyfwjGpbTZB5C64ONEpPZBGE8OjFWSCjJgSTsw6SwZDZD'
  center = (51.513855129521,-0.12574267294645)
  distance = 500
  places = get_places(token, center, distance)

  categories = set()
  for p in places:
    categories.add(p['category'])
    for c in p['category_list']:
      categories.add(c['name'])
  print categories
  return HttpResponse(json.dumps(places))

@require_POST
def logout_view(request):
  if request.user.is_authenticated():
    logout(request)
  messages.info(request, 'You are now logged out.')
  return HttpResponseRedirect(url_reverse('home'))


def _verdict_ok(response):
  return {
    'verdict': 'ok',
    'message': response
  }


def _verdict_error(message):
  return {
    'verdict': 'error',
    'message': message
  }


@ajax_decorator
def near_location(request, location):
  return _verdict_ok({'received':location})


def login_view(request, accessToken, userID, **kwargs):
  try:
    user = User.objects.get(username=userID)
  except User.DoesNotExist:
    graph = facebook.GraphAPI(accessToken)
    profile = graph.get_object('me')
    user = User.objects.create_user(userID, profile['email'], userID)
    try:
      user.first_name = profile['first_name']
      user.last_name = profile['last_name']
    except KeyError:
      pass
    user.save()

  try:
    user_meta = UserMeta.objects.get(user=user)
  except UserMeta.DoesNotExist:
    user_meta = UserMeta(user=user, fb_token=accessToken)
    user_meta.save()

  user = authenticate(username=userID, password=userID)
  login(request, user)
  return HttpResponseRedirect(url_reverse('home'))


data_providers = {
  'near_location': near_location,
  'login': login_view,
}


def data_provider(request, action):
  if request.is_ajax():
    try:
      payload = json.loads(request.REQUEST.get('payload', '{}'))
    except ValueError:
      response = {'verdict': 'error', 'message': 'Invalid payload'}
      return HttpResponse(json.dumps(response))

    if action in data_providers:
      data_provider = data_providers.get(action)
      try:
        return data_provider(request, **payload)
      except TypeError:
        # Most likely missing or extra payload arguments
        response = {
          'verdict': 'error',
          'message': 'Invalid payload or 500 internal error (TypeError)'
        }
        return HttpResponse(json.dumps(response))
    else:
      response = {'verdict': 'error', 'message': 'Unrecognized action'}
      return HttpResponse(json.dumps(response))
  else:
    raise Http404
