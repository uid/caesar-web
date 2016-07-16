import os
import datetime
from chunks.models import Chunk, Assignment, Milestone, Semester

from accounts.fields import MarkdownTextField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ObjectDoesNotExist

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver

class Extension(models.Model):
    user = models.ForeignKey(User, related_name='extensions')
    milestone = models.ForeignKey(Milestone, related_name='extensions')
    slack_used = models.IntegerField(default=0, blank=True, null=True)

    def assignment(self):
        return self.milestone.assignment

    def new_duedate(self):
        return self.milestone.duedate + datetime.timedelta(days=self.slack_used)

    def __str__(self):
      return '%s (%s) %s days' % (self.user.username, self.milestone.full_name(), self.slack_used)

class Member(models.Model):
    STUDENT = 'S'
    TEACHER = 'T'
    VOLUNTEER = 'V'
    ROLE_CHOICES = (
        (STUDENT, 'student'),
        (TEACHER, 'teacher'),
        (VOLUNTEER, 'volunteer'),
    )

    role = models.CharField(max_length=1, choices=ROLE_CHOICES)
    slack_budget = models.IntegerField(default=5, blank=False, null=False)
    user = models.ForeignKey(User, related_name='membership')
    semester = models.ForeignKey(Semester, related_name='members')

    def __str__(self):
      return '%s (%s), %s' % (self.user.username, self.get_role_display(), self.semester)

    def is_student(self):
        return self.role == Member.STUDENT

    def is_teacher(self):
        return self.role == Member.TEACHER

    def is_volunteer(self):
        return self.role == Member.VOLUNTEER

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    reputation = models.IntegerField(default=0, editable=True)

    def __unicode__(self):
        return self.user.__unicode__()

    def name(self):
      if self.user.first_name and self.user.last_name:
        return self.user.first_name + ' ' + self.user.last_name
      return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        profile, created = UserProfile.objects.get_or_create(user=instance)
        if created:
            profile.save()

