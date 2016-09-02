from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from review.models import *

admin.site.unregister(User)
UserAdmin.list_display += ('date_joined', 'last_login',)
UserAdmin.list_filter += ('date_joined', 'last_login',)
class UserProfileInline(admin.StackedInline):
    model = UserProfile
class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]
admin.site.register(User, UserProfileAdmin)

class MemberAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'semester__semester', 'semester__subject__name')
    raw_id_fields = ('user',)
admin.site.register(Member, MemberAdmin)

class ExtensionAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
admin.site.register(Extension, ExtensionAdmin)

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester')
    search_fields = ('name', 'semester')
admin.site.register(Assignment, AssignmentAdmin)

class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ('authors__username',)
admin.site.register(Submission, SubmissionAdmin)

class ChunkAdmin(admin.ModelAdmin):
    list_display = ('name', 'file', 'start', 'end', 'class_type', 'staff_portion', 'student_lines', 'chunk_info')
    search_fields = ('name', 'file__path', 'file__submission__name')
    raw_id_fields = ('file',)
admin.site.register(Chunk, ChunkAdmin)

class StaffMarkerAdmin(admin.ModelAdmin):
    list_display = ('chunk', 'start_line', 'end_line')
    raw_id_fields = ('chunk',)
admin.site.register(StaffMarker, StaffMarkerAdmin)

class MilestoneAdmin(admin.ModelAdmin):
    def extension_data(self, obj):
        num_no_extensions = Member.objects.filter(semester=obj.assignment.semester, role=Member.STUDENT)\
            .exclude(user__extensions__milestone=obj).count()
        extensions = str(num_no_extensions)
        for num_days in range(1, obj.max_extension+1):
            num_extensions = Extension.objects.filter(milestone=obj).filter(slack_used=num_days).count()
            extensions += ' / ' + str(num_extensions)
        return '<a href="%s%s">%s</a>' % ('/all_extensions/', obj.id, extensions)
    extension_data.allow_tags = True
    extension_data.short_description = 'Extensions (0 Days / 1 Day / 2 Days / ...)'

class ReviewMilestoneAdmin(MilestoneAdmin):
    list_display = ('__unicode__', 'extension_data', 'routing_link', 'list_users_link',)
    def routing_link(self, obj):
        return '<a href="%s%s">%s</a>' % ('/simulate/', obj.id, 'Configure Routing')
    routing_link.allow_tags = True
    routing_link.short_description = 'Configure Routing'
    def list_users_link(self, obj):
        return '<a href="%s%s">%s</a>' % ('/list_users/', obj.id, 'List Users')
    list_users_link.allow_tags = True
    list_users_link.short_description = 'List Users'
    exclude = ('type',)
admin.site.register(ReviewMilestone, ReviewMilestoneAdmin)

class SubmitMilestoneAdmin(MilestoneAdmin):
    list_display = ('__unicode__', 'extension_data',)
    exclude = ('type',)
admin.site.register(SubmitMilestone, SubmitMilestoneAdmin)


class FileAdmin(admin.ModelAdmin):
    search_fields = ('path','submission__authors__username',)
    raw_id_fields = ('submission',)
admin.site.register(File, FileAdmin)

admin.site.register(Batch)
admin.site.register(Subject)
admin.site.register(Semester)
admin.site.register(ChunkReview)

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'reviewer', 'submission', 'chunk')
    fields = ('chunk', 'submission', 'reviewer', 'status', 'milestone', 'created', 'opened', 'started', 'completed',)
    readonly_fields = ('created', 'opened', 'started', 'completed')
    search_fields = ('reviewer__username', 'submission__authors__username', 'milestone__assignment__semester__semester', 'milestone__assignment__semester__subject__name','milestone__assignment__name')
    raw_id_fields = ('submission', 'chunk', 'chunk_review', 'reviewer',)
admin.site.register(Task, TaskAdmin)

class VoteInline(admin.TabularInline):
    model = Vote
    raw_id_fields = ('comment', 'author', )
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
    raw_id_fields = ('submission', 'comment', 'recipient',)
admin.site.register(Notification, NotificationAdmin)
