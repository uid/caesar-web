from django.contrib import admin

from tasks.models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'reviewer', 'chunk')
    fields = ('chunk', 'reviewer', 'status', 'due', 'created', 'opened', 'started', 'completed',)
    readonly_fields = ('created', 'opened', 'started', 'completed')

admin.site.register(Task, TaskAdmin)
