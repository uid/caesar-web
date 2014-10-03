import datetime
import logging
from django.http import HttpResponse

from userlogging.models import CommentSearchLog
from review.models import Comment

def log_comment_search(request):
    comment = Comment.objects.get(id=request.POST['comment_id'])
    entry = CommentSearchLog(user=request.user, action=request.POST['action'], comment=comment, timestamp=datetime.datetime.now())
    entry.save()
    return HttpResponse()
