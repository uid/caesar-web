from django.contrib import admin

from accounts.models import Extension, Member
from chunks.models import Assignment, ReviewMilestone, SubmitMilestone, Submission, File, Chunk, StaffMarker, Batch, Subject, Semester

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester')
    search_fields = ('name', 'semester')

class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ('authors__username',)

class ChunkAdmin(admin.ModelAdmin):
    list_display = ('name', 'file', 'start', 'end', 'class_type', 'staff_portion', 'student_lines', 'chunk_info')
    search_fields = ('name', 'file__path', 'file__submission__name')

class StaffMarkerAdmin(admin.ModelAdmin):
    list_display = ('chunk', 'start_line', 'end_line')

class MilestoneAdmin(admin.ModelAdmin):
	def extension_data(self, obj):
		num_no_extensions = Member.objects.filter(semester=obj.assignment.semester, role=Member.STUDENT)\
			.exclude(user__extensions__milestone=obj).count()
		extensions = str(num_no_extensions)
		for num_days in range(1, obj.max_extension+1):
			num_extensions = Extension.objects.filter(milestone=obj).filter(slack_used=num_days).count()
			extensions += ' / ' + str(num_extensions)
		return '<a href="%s%s">%s</a>' % ('/accounts/all_extensions/', obj.id, extensions)
	extension_data.allow_tags = True
	extension_data.short_description = 'Extensions (0 Days / 1 Day / 2 Days / ...)'

class ReviewMilestoneAdmin(MilestoneAdmin):
	list_display = ('__unicode__', 'extension_data', 'review_info_link', 'routing_link', 'list_users_link',)
	def review_info_link(self, obj):
		return '<a href="%s%s">%s</a>' % ('/tasks/review_milestone_info/', obj.id, 'Review Info')
	review_info_link.allow_tags = True
	review_info_link.short_description = 'Review Info'
	def routing_link(self, obj):
		return '<a href="%s%s">%s</a>' % ('/chunks/simulate/', obj.id, 'Configure Routing')
	routing_link.allow_tags = True
	routing_link.short_description = 'Configure Routing'
	def list_users_link(self, obj):
		return '<a href="%s%s">%s</a>' % ('/chunks/list_users/', obj.id, 'List Users')
	list_users_link.allow_tags = True
	list_users_link.short_description = 'List Users'
	exclude = ('type',)

class SubmitMilestoneAdmin(MilestoneAdmin):
	list_display = ('__unicode__', 'extension_data',)
	exclude = ('type',)

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(ReviewMilestone, ReviewMilestoneAdmin)
admin.site.register(SubmitMilestone, SubmitMilestoneAdmin)
admin.site.register(File)
admin.site.register(Batch)
admin.site.register(Chunk, ChunkAdmin)
admin.site.register(StaffMarker, StaffMarkerAdmin)
admin.site.register(Subject)
admin.site.register(Semester)
