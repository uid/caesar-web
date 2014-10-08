import datetime
from django.http import HttpResponse

from log.models import Log

def log(request):
    if request.is_ajax():
      entry = Log(user=request.user, log=request.POST, timestamp=datetime.datetime.now())
      entry.save()
    return HttpResponse()

def aggregateLog(timestart, timestop, user):
    logs = Logging.objects.filter(user=user, timestamp__gte=timestart, timestamp__lte=timestop)
    log = [l.log for l in logs]
    aggregateLog = Log(user=user, log=str(log), timestamp=timestop)