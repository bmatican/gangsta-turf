from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.core.urlresolvers import reverse as url_reverse
from django.core import serializers
from django.db import transaction, IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
import facebook

import json

from coldruins.web.decorators import *
from coldruins.web.models import *
from coldruins.web.fbgraph import *

@process_event_decorator
@ensure_csrf_cookie
def home(request):
  user_data = ''
  if request.user != None and request.user.is_authenticated():
    user_data = '<script>window.userid={}</script>'.format(request.user.id)
    if request.user.meta.clan != None:
      user_data += '<script>window.userclan={}</script>'.format(request.user.meta.clan.id)
    resources = list(request.user.meta.get_resources())
    user_data += '<script>window.userresources={}</script>'.format(resources)
    user_data += '<script>window.userattackingunits={}</script>'.format(
        request.user.meta.get_attacking_units())
  return HttpResponse(
      open('coldruins/web/static/index.html', 'rt').read() + user_data)

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
def near_location(request, center, distance):
  return _get_locations(request, center, distance)


def _get_locations(request, center, distance):
  # token = 'BAACEdEose0cBAKaRmOZBE29VpXfFHYgZCsWP2zyw7aoQ8GdZBeYtTMiAdbFitCYZA2FM34xoL7MkZC6cfoFQR0dTUx1sBpZCYnyrScZCyZCN4k2ZAMCo1rdS1sxYJqDYjbeOpPlANc1KEurCDSaSFWEbWHRPvOyHzZAZAPGyuMEzCVUQktFj9FdlDEHV0vGXh11ZA78iMdEuPYZBwyuwKaH6U5Fb2hcNeckuEzm9tBa6SZCWOsxAZDZD'
  try:
    user_meta = UserMeta.objects.get(user=request.user)
    token = user_meta.fb_token
  except UserMeta.DoesNotExist:
    return _verdict_error('Invalid/missing token')
  # center = '51.513855129521,-0.12574267294645'
  # distance = 500
  places = get_places(token, center, distance)

  response = []
  for p in places:
    try:
      loc = Location.objects.get(fb_id=p['id'])
      response.append(loc)
      continue
    except Location.DoesNotExist:
      pass

    try:
      categories = [p['category']]
      for c in [cat['name'] for cat in p['category_list']]:
        categories.append(c)

      category = 4 # sensible default :))
      potential_cat = {}
      for c in categories:
        low = c.lower()
        if 'restaurant' in low or \
          ' bar' in low or \
          'bar ' in low or \
          'bar' == low:
          category = 1
          potential_cat = {}
          break
        elif c in static_categories:
          key = static_categories[c]
          val = potential_cat.setdefault(key, 0)
          potential_cat[key] = val + 1
      val_max = 0
      # this gets ignored if we found a bar/restaurant
      for cat, val in potential_cat.iteritems():
        if val > val_max:
          category = cat
          val_max = val

      l = Location(
        fb_id = p['id'],
        name = p['name'],
        lat = p['latitude'],
        lon = p['longitude'],
        category = category
      )
      l.save()
      response.append(l)
    except IntegrityError:
      pass
  ret = [l.export() for l in response]
  return _verdict_ok(ret)


@ajax_decorator
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
  user_meta.fb_token = accessToken
  user_meta.save()

  user = authenticate(username=userID, password=userID)
  login(request, user)
  return HttpResponseRedirect(url_reverse('home'))


@ajax_decorator
def get_location_data(request, location_id):
  troops = Troops.get_troops(location_id)
  return troops


@ajax_decorator
def make_troops(request, location_db_id, unit_id, count):
  Troops.make_troops(request.user.id, location_db_id, unit_id, count)


@ajax_decorator
def buy_troops(request, unit_id, numbers):
  if unit_id not in UNITS:
    return _verdict_error('Invalid unit id')
  else:
    remaining = request.user.meta.buy_troops(unit_id, numbers)
    if remaining == None:
      return _verdict_error('Not enough resources')
    else:
      return _verdict_ok({'resources_left': list(remaining)})


@ajax_decorator
def checkin(request, location_id):
  response = Checkin.make_checkin(request.user.meta, location_id)
  return _verdict_ok(response)

@ajax_decorator
def facepile(request):
  token = request.user.meta.fb_token
  g = Graph(token, 'me')
  return _verdict_ok(g.friends())

@ajax_decorator
def attack(request, location_id):
  response = OngoingFight.new_fight(request.user.meta, location_id)
  return _verdict_ok(response)


@ajax_decorator
def get_fighting_powers(request, location_id):
  response = OngoingFight.get(location=location_id).fighting_powers
  return _verdict_ok(response[0])


data_providers = {
  'login': login_view,
  'near_location': near_location,

  'buy_troops': buy_troops,
  'make_troops': make_troops,

  'get_location_data': get_location_data,
  'facepile' : facepile,
  'checkin': checkin,
  'attack': attack,
  'get_fighting_powers': get_fighting_powers,
}

@process_event_decorator
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
