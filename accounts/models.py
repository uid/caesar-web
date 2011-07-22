import os

from chunks.models import Chunk

from sorl.thumbnail import ImageField

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver

class UserProfile(models.Model):
    def get_photo_path(instance, filename):
        return os.path.join(
                settings.PROFILE_PHOTO_DIR, 
                instance.user.username, 
                filename)

    user = models.OneToOneField(User)
    photo = ImageField(upload_to=get_photo_path)
    assigned_chunks = models.ManyToManyField(Chunk, through='tasks.Task',
        related_name='reviewers')
    reputation = models.IntegerField(default=0, editable=False)
    
    def __unicode__(self):
        return self.user.__unicode__()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)
