from django.db import models
from django.contrib.auth.models import User
from review.models import Comment

class CommentSearchLog(models.Model):
    user = models.ForeignKey(User)
    action = models.CharField(max_length=50)
    comment = models.ForeignKey(Comment, related_name='comment_search_log', default=None)
    timestamp = models.DateField()
