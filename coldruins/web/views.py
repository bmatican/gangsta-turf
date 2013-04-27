from django.contrib.auth import logout
from django.conf import settings
from django.core.urlresolvers import reverse as url_reverse
from django.db import transaction, IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import ensure_csrf_cookie

import json

from coldruins.web.decorators import *

def home(request):
  return HttpResponse(
      open('coldruins/web/static/index.html', 'rt').read())

@require_POST
def logout_view(request):
  if request.user.is_authenticated():
    logout(request)
  messages.info(request, 'You are now logged out.')
  return HttpResponseRedirect(url_reverse('home'))
##############################################################################
def _verdict_ok(response):
  return {
    'verdict':'ok',
    'message':response
  }

def _verdict_error(message):
  return {
    'verdict':'error',
    'message':message
  }

def near_location(request, location):
  return _verdict_ok({'received':location})

def login(request, auth_response):
  return {}

data_providers = {
  'near_location': near_location,
  'login': login
}

@ensure_csrf_cookie
@ajax_decorator
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
