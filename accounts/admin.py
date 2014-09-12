from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from accounts.models import UserProfile, Member, Extension
from sorl.thumbnail.admin import AdminImageMixin

admin.site.unregister(User)

class UserProfileInline(AdminImageMixin, admin.StackedInline):
    model = UserProfile

class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]

UserAdmin.list_display += ('date_joined', 'last_login',)
UserAdmin.list_filter += ('date_joined', 'last_login',)

class MemberAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'semester__semester', 'semester__subject__name')

class ExtensionAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)

admin.site.register(User, UserProfileAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Extension, ExtensionAdmin)

