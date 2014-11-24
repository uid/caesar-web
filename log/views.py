import datetime
from django.http import HttpResponse
import json

from log.models import Log

def log(request):
    if request.is_ajax():
      entry = Log(user=request.user, log=json.dumps(request.POST), timestamp=datetime.datetime.now())
      entry.save()
    return HttpResponse()
