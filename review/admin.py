from django.contrib import admin
from review.models import Comment, Vote, Notification

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
