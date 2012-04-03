from django.contrib import admin

from chunks.models import Assignment, Submission, File, Chunk, StaffMarker, ChunkProfile

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'duedate', 'code_review_end_date', 'semester', 'student_count', 'alum_count', 'staff_count')
    search_fields = ('name', 'semester')

class ChunkAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'file', 'start', 'end', 'created', 'modified', 'staff_portion', 'class_type')
    list_display = ('name', 'file', 'start', 'end', 'class_type', 'staff_portion')
    search_fields = ('name', 'file__path', 'file__submission__name')

class StaffMarkerAdmin(admin.ModelAdmin):
    list_display = ('chunk', 'start_line', 'end_line')

class ChunkProfileAdmin(admin.ModelAdmin):
    list_display = ('chunk', 'student_lines', 'return_count', 
    'for_nesting_depth', 'if_nesting_depth', 'synchronized_count',
    'valid', 'viable_comments', 'static_comments', 'comment_words')

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission)
admin.site.register(File)
admin.site.register(Chunk, ChunkAdmin)
admin.site.register(StaffMarker, StaffMarkerAdmin)
admin.site.register(ChunkProfile, ChunkProfileAdmin)
