from django.conf.urls.defaults import *

urlpatterns = patterns('dashboard.views',
    (r'^$', 'dashboard'),
    (r'^dashboard/(?P<username>\w+)', 'student_dashboard'),
)

