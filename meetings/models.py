from django.db import models
from django.contrib.auth.models import User
from accounts.models import User Profile
import datetime

MEETING_STATUS_CHOICES = (
        ('S', 'Scheduled'),
        ('I', 'In Progress'),
        ('F', 'Finished'),
        ('D', 'Deleted'),
    )

class Meeting(models.Model):
    meeting_start_datetime = models.DateTimeField('Meeting Start Date Time')
    meeting_status = models.CharField(max_length=1,
                                      choices=MEETING_STATUS_CHOICES,
                                      default='S')
    meeting_duration = models.IntegerField()
    meeting_end_datetime = models.DateTimeField('Meeting End Date Time')
    meeting_name = models.CharField(max_length=128)
    meeting_key = models.CharField(max_length=128)
    meeting_password = models.CharField(max_length=128)
    meeting_host_url = models.CharField(max_length=128)
    meeting_attendee_url = models.CharField(max_length=128)
    users = models.ManyToManyField(UserProfile)
    def get_url(self, user):
        if user.profile.is_student():
            return self.meeting_host_url
        else:
            template = "{prefix}&AE={email}&AN={username}"
            return template.format(prefix=self.meeting_attendee_url, email=user.email,
                                   username=user.username)
    
