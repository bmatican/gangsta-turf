from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST

import json

from coldruins.web.models import TroopMovement, Location, OngoingFight


def process_event_decorator(f):
  def wrap(*args, **kwargs):
    TroopMovement.move_pending_troops()
    Location.make_pending_payments()
    OngoingFight.end_pending_fights()
    return f(*args, **kwargs)
  return wrap


def ajax_decorator(f):
  """Decorator which should be used on AJAX data providers.
  Processes the provider's output, json serializes and wraps it around
  in a HttpResponse if needed.
  """

  def wrap(*args, **kwargs):
    response = f(*args, **kwargs)
    if isinstance(response, HttpResponse):
      return response
    if isinstance(response, dict):
      response = json.dumps(response)
    return HttpResponse(response)
  return wrap
