from django.contrib import admin

from chunks.models import Assignment, Submission, File, Chunk, StaffMarker, ChunkProfile

class AssignmentAdmin(admin.ModelAdmin):
    pass

class ChunkAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'file', 'start', 'end', 'created', 'modified')
    list_display = ('name', 'file', 'start', 'end')
    search_fields = ('name', 'file__path', 'file__submission__name')

class StaffMarkerAdmin(admin.ModelAdmin):
    list_display = ('chunk', 'start_line', 'end_line')

class ChunkProfileAdmin(admin.ModelAdmin):
    list_display = ('chunk', 'semicolons', 'nesting_depth', 
    'total_function_calls', 'total_branches', 'total_loops',
    'todo_count', 'null_count', 'instanceof_count', 'synchronized_count',
    'valid', 'viable_comments', 'static_comments', 'iterator_count', 'comment_words')

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission)
admin.site.register(File)
admin.site.register(Chunk, ChunkAdmin)
admin.site.register(StaffMarker, StaffMarkerAdmin)
admin.site.register(ChunkProfile, ChunkProfileAdmin)
