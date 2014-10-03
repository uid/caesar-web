from django.contrib import admin

from accounts.models import Member
from userlogging.models import CommentSearchLog

class CommentSearchLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'comment', 'timestamp')
    search_fields = ('comment', 'action', 'user__username', 
            'user__first_name', 'user__last_name')

admin.site.register(CommentSearchLog, CommentSearchLogAdmin)
