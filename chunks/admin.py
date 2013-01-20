from django.contrib import admin

from chunks.models import Assignment, Submission, File, Chunk, StaffMarker, Batch, Subject, Semester

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'duedate', 'code_review_end_date', 'semester', 'student_count', 'alum_count', 'staff_count')
    search_fields = ('name', 'semester')

class ChunkAdmin(admin.ModelAdmin):
    list_display = ('name', 'file', 'start', 'end', 'class_type', 'staff_portion', 'student_lines', 'chunk_info')
    search_fields = ('name', 'file__path', 'file__submission__name')

class StaffMarkerAdmin(admin.ModelAdmin):
    list_display = ('chunk', 'start_line', 'end_line')

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission)
admin.site.register(File)
admin.site.register(Batch)
admin.site.register(Chunk, ChunkAdmin)
admin.site.register(StaffMarker, StaffMarkerAdmin)
admin.site.register(Subject)
admin.site.register(Semester)
