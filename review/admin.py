from django.contrib import admin
from review.models import Comment, Vote, Task

class VoteInline(admin.TabularInline):
    model = Vote

class CommentAdmin(admin.ModelAdmin):
    inlines = [ VoteInline ]
    list_display = ('id', 'chunk', 'start', 'end', 'type', 'author', 'text')
    search_fields = ('chunk__name', 'text', 'author__username', 
            'author__first_name', 'author__last_name')

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'reviewer', 'chunk')
    fields = ('chunk', 'reviewer', 'status', 'due', 'created', 'opened', 'started', 'completed',)
    readonly_fields = ('created', 'opened', 'started', 'completed')

admin.site.register(Comment, CommentAdmin)
admin.site.register(Task, TaskAdmin)
