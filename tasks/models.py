from datetime import datetime

from django.db import models
from django.db.models import Count

from accounts.models import UserProfile
from chunks.models import Chunk, ReviewMilestone
import app_settings

class Task(models.Model):
    STATUS_CHOICES=(
        ('N', 'New'),
        ('O', 'Opened'),
        ('S', 'Started'),
        ('C', 'Completed'),
        ('U', 'Unfinished'),
    )
    chunk = models.ForeignKey(Chunk, related_name='tasks')
    reviewer = models.ForeignKey(UserProfile, related_name='tasks')
    milestone = models.ForeignKey(ReviewMilestone, related_name='tasks')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='N')
    # TODO switch to a more robust model history tracking (e.g. versioning)
    created = models.DateTimeField(auto_now_add=True)
    opened = models.DateTimeField(blank=True, null=True)
    started = models.DateTimeField(blank=True, null=True)
    completed = models.DateTimeField(blank=True, null=True)
    class Meta:
        unique_together = ('chunk', 'reviewer',)

    def __unicode__(self):
        return "Task: %s - %s" % (self.reviewer.user, self.chunk)

    def mark_as(self, status):
        if status not in zip(*Task.STATUS_CHOICES)[0]:
            raise Exception('Invalid task status')

        self.status = status
        if status == 'N':
            self.opened = None
            self.started = None
            self.completed = None
        elif status == 'O':
            self.opened = datetime.now()
        elif status == 'S':
            self.started = datetime.now()
        elif status == 'C':
            self.completed = datetime.now()

        self.save()

    def author(self):
      return self.chunk.file.submission.author
