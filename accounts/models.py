import os
import datetime
from chunks.models import Chunk

from sorl.thumbnail import ImageField

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver

class Token(models.Model):
    expire = models.DateTimeField(null=True, blank=True)
    code = models.CharField(null=True, blank=True, max_length=20)

class UserProfile(models.Model):
    # def get_photo_path(instance, filename):
    #     return os.path.join(
    #             settings.PROFILE_PHOTO_DIR, 
    #             instance.user.username, 
    #             filename)

    ROLE_CHOICES = (
        ('T', 'Teaching staff'),
        ('S', 'Student'),
    )
    SEMESTER_CHOICES = (
        ('FA11', "Fall 2011"),
        ('SP12', "Spring 2012"),
        ('FA12', "Fall 2012"),
        ('SP13', "Spring 2013"),
    )
    user = models.OneToOneField(User, related_name='profile')
    # photo = ImageField(upload_to=get_photo_path)
    assigned_chunks = models.ManyToManyField(Chunk, through='tasks.Task',
        related_name='reviewers')
    reputation = models.IntegerField(default=0, editable=True)
    role = models.CharField(max_length=1, choices=ROLE_CHOICES,
                            blank=True, null=True)
    extension_days = models.IntegerField(default=5)
    semester_taken = models.CharField(max_length=4, choices=SEMESTER_CHOICES, 
                                      blank=True, null=True)
    
    token = models.ForeignKey(Token, related_name='invited', default=None, null=True)
    def __unicode__(self):
        return self.user.__unicode__()

    def is_staff(self):
        return self.role == 'T'

    def is_student(self):
        return self.role == 'S'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)
        if created:
            profile.role = 'S'
            profile.save()
    