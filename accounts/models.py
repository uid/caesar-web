import os
import datetime
from chunks.models import Chunk, Assignment, Milestone, Semester

from sorl.thumbnail import ImageField
from accounts.fields import MarkdownTextField
from accounts.storage import OverwriteStorage
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ObjectDoesNotExist

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver

class Token(models.Model):
    expire = models.DateTimeField(null=True, blank=True)
    code = models.CharField(null=True, blank=True, max_length=20)

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
    role = models.CharField(max_length=16)
    slack_budget = models.IntegerField(default=5, blank=False, null=False)
    user = models.ForeignKey(User, related_name='membership')
    semester = models.ForeignKey(Semester, related_name='members')

    def __str__(self):
      return '%s (%s), %s' % (self.user.username, self.role, self.semester)

class UserProfile(models.Model):
    def get_photo_path(instance, filename):
        return os.path.join(
                settings.PROFILE_PHOTO_DIR,
                instance.user.username)

    ROLE_CHOICES = (
        ('T', 'Teaching staff'),
        ('S', 'Student'),
        ('A', 'Alumni'),
    )
    user = models.OneToOneField(User, related_name='profile')
    
    assigned_chunks = models.ManyToManyField(Chunk, through='tasks.Task',
        related_name='reviewers')
    reputation = models.IntegerField(default=0, editable=True)
    role = models.CharField(max_length=1, choices=ROLE_CHOICES,
                            blank=True, null=True)

    photo = models.ImageField(upload_to=get_photo_path, storage=OverwriteStorage(), blank=True, null=True,\
        help_text='Use a JPEG or PNG photo.')
    about = MarkdownTextField(allow_html=False, blank=True, \
        help_text='Format using <a href="http://stackoverflow.com/editing-help">Markdown</a>.')
    company = models.CharField(max_length=100, default='MIT', blank=True)
    class_year = models.IntegerField(validators=[MinValueValidator(1920), MaxValueValidator(2050)], null=True, blank=True)

    # social network links
    twitter = models.CharField(max_length=16, blank=True, \
        help_text='username. (ex.) ben-bitdiddle')
    github = models.CharField(max_length=30, blank=True, \
        help_text='username. (ex.) bitdiddle')
    linkedin = models.URLField(blank=True,\
        help_text='public profile URL. (ex.) http://www.linkedin.com/in/kiranbhattaram/')
    website = models.URLField(blank=True,\
        help_text='URL')

    token = models.ForeignKey(Token, related_name='invited', default=None, null=True)
    def __unicode__(self):
        return self.user.__unicode__()

    def is_staff(self):
        return self.role == 'T'

    def is_student(self):
        return self.role == 'S'

    def is_alum(self):
        return not is_staff() and not is_student() and not is_checkstyle()

    def role_str(self):
      if self.is_student():
        return 'Student'
      elif self.is_staff():
        return 'Staff'
      return 'Other'

    def is_checkstyle(self):
      return self.user.username == 'checkstyle'

    def name(self):
      if self.user.first_name and self.user.last_name:
        return self.user.first_name + ' ' + self.user.last_name
      return self.user.username

    def extension_days(self):
      total_days = 10 #TODO: change after multi-class refactor
      used_days = sum([extension.slack_used for extension in self.user.extensions.all()])
      return total_days - used_days

    def get_user_duedate(self, milestone):
        try:
            user_extension = milestone.extensions.get(user=self.user)
            return user_extension.new_duedate()
        except ObjectDoesNotExist:
            return milestone.duedate


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)
        if created:
            profile.save()

