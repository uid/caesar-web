from django.contrib import admin

from tasks.models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'reviewer', 'submission', 'chunk')
    fields = ('chunk', 'submission', 'reviewer', 'status', 'milestone', 'created', 'opened', 'started', 'completed',)
    readonly_fields = ('created', 'opened', 'started', 'completed')
    search_fields = ('reviewer__user__username', 'submission__authors__username', 'milestone__assignment__semester__semester', 'milestone__assignment__semester__subject__name','milestone__assignment__name')

admin.site.register(Task, TaskAdmin)
