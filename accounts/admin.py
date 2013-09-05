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

admin.site.register(User, UserProfileAdmin)
admin.site.register(Member)
admin.site.register(Extension)
