import datetime
from django.http import HttpResponse

from log.models import Log

def log(request):
    if request.is_ajax():
      entry = Log(user=request.user, log=request.POST, timestamp=datetime.datetime.now())
      entry.save()
    return HttpResponse()

def markLogStart(user):
    logStart = Log(user=user, log='LOGSTART', timestamp=datetime.datetime.now())
    logStart.save()

def aggregateLog(user):
    logStart = Logging.objects.get(log='LOGSTART')
    timestart = logStart.timestamp
    logStart.delete()
    logs = Logging.objects.filter(user=user, timestamp__gte=timestart)
    logList = [l.log for l in logs]
    aggregateLog = Log(user=user, log=str(logList), timestamp=datetime.datetime.now())
    aggregateLog.save()
    logs.delete()