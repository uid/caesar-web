import datetime
from django.http import HttpResponse

from log.models import Log

def log(request):
    if request.is_ajax():
      entry = Log(user=request.user, log=request.POST, timestamp=datetime.datetime.now())
      entry.save()
    return HttpResponse()
