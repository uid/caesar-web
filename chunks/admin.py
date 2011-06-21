from django.contrib import admin

from chunks.models import Assignment, Submission, File, Chunk

class AssignmentAdmin(admin.ModelAdmin):
    pass

class ChunkAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'file', 'start', 'end', 'created', 'modified')
    list_display = ('name', 'file', 'start', 'end')
    search_fields = ('name', 'file__path', 'file__submission__name')

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission)
admin.site.register(File)
admin.site.register(Chunk, ChunkAdmin)
