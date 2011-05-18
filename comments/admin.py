from django.contrib import admin
from caesar.comments.models import Comment, Vote

class VoteInline(admin.TabularInline):
    model = Vote

class CommentAdmin(admin.ModelAdmin):
    inlines = [ VoteInline ]
    list_display = ('id', 'chunk', 'start', 'end', 'type', 'author', 'text')

admin.site.register(Comment, CommentAdmin)
