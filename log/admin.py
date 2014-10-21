from django.contrib import admin

from accounts.models import Member
from log.models import Log

class LogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'log', 'timestamp')
    search_fields = ('log', 'user__username', 
            'user__first_name', 'user__last_name')

admin.site.register(Log, LogAdmin)
