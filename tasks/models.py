from datetime import datetime

from django.db import models
from django.db.models import Count

from accounts.models import UserProfile
from chunks.models import Chunk
import app_settings

class TaskManager(models.Manager):
    def assign_tasks(self, assignment, user):
        """
        Assigns chunks to the user for review, if the user does not have enough.

        Returns the number of chunks assigned.
        """
        reviewer = user.get_profile()
        current_task_count = Task.objects.filter(reviewer=reviewer, 
                chunk__file__submission__assignment=assignment).count()
        
        assign_count = app_settings.CHUNKS_PER_REVIEWER - current_task_count
        if assign_count <= 0:
            return assign_count
        
        # FIXME this query will probably need to be optimized
        chunks = Chunk.objects.exclude(file__submission__name=user.username) \
            .filter(file__submission__assignment=assignment) \
            .exclude(tasks__reviewer=reviewer) \
            .annotate(reviewer_count=Count('tasks')) \
            .filter(reviewer_count__lt=app_settings.REVIEWERS_PER_CHUNK) \
            .order_by('-reviewer_count')[0:assign_count]
        for chunk in chunks:
            task = Task(reviewer=user.get_profile(), chunk=chunk)
            task.save()
            
        return assign_count

class Task(models.Model):
    STATUS_CHOICES=(
        ('N', 'New'),
        ('O', 'Opened'),
        ('S', 'Started'),
        ('C', 'Completed'),
    )
    chunk = models.ForeignKey(Chunk, related_name='tasks')
    reviewer = models.ForeignKey(UserProfile, related_name='tasks')
    due = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='N')
    # TODO switch to a more robust model history tracking (e.g. versioning)
    created = models.DateTimeField(auto_now_add=True)
    opened = models.DateTimeField(blank=True, null=True)
    started = models.DateTimeField(blank=True, null=True)
    completed = models.DateTimeField(blank=True, null=True)
    objects = TaskManager()
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
