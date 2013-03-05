'''
Created on Jan 1, 2013

@author: graves
'''
from django.contrib import admin
from models import Meeting
from models import UserProfile

admin.site.register(Meeting)
admin.site.register(UserProfile)