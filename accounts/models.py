import os

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    photo = models.ImageField(upload_to=get_photo_path)

    def get_photo_path(instance, filename):
        return os.path.join(
                settings.PROFILE_PHOTO_DIR, 
                instance.user.username, 
                filename)
