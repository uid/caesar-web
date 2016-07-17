from django.contrib import admin
from review.models import *

admin.site.register(ChunkReview)

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'reviewer', 'submission', 'chunk')
    fields = ('chunk', 'submission', 'reviewer', 'status', 'milestone', 'created', 'opened', 'started', 'completed',)
    readonly_fields = ('created', 'opened', 'started', 'completed')
    search_fields = ('reviewer__username', 'submission__authors__username', 'milestone__assignment__semester__semester', 'milestone__assignment__semester__subject__name','milestone__assignment__name')

admin.site.register(Task, TaskAdmin)

class VoteInline(admin.TabularInline):
    model = Vote

class CommentAdmin(admin.ModelAdmin):
    inlines = [ VoteInline ]
    list_display = ('id', 'chunk', 'start', 'end', 'type', 'author', 'text')
    search_fields = ('chunk__name', 'text', 'author__username', 
            'author__first_name', 'author__last_name')
    raw_id_fields = ('chunk', 'author', 'batch', 'parent', 'similar_comment')

admin.site.register(Comment, CommentAdmin)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'created', 'reason', 'comment', 'submission', 'email_sent')
    search_fields = ('comment', 'submission', 'recipient')

admin.site.register(Notification, NotificationAdmin)
