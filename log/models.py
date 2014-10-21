from django.db import models
from django.contrib.auth.models import User

class Log(models.Model):
    user = models.ForeignKey(User)
    log = models.TextField()
    timestamp = models.DateTimeField()