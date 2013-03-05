from django.conf.urls.defaults import url, patterns, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'meetings.views.index'),
    url(r'^delete/(?P<meeting_key>\d+)', 'meetings.views.delete'),
    url(r'^edit/(?P<meeting_key>\d+)', 'meetings.views.edit'),
    url(r'^view/', 'meetings.views.view'),
    url(r'^schedule/', 'meetings.views.schedule'),
)
