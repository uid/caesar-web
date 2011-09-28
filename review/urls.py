from django.conf.urls.defaults import *

urlpatterns = patterns('review.views',
    (r'^$', 'dashboard'),
    (r'^stats/', 'stats'),
    (r'^new_comment/', 'new_comment'),
    (r'^change_task/', 'change_task'),
    (r'^reply/', 'reply'),
    (r'^delete_comment/', 'delete_comment'),
    (r'^vote/', 'vote'),
    (r'^unvote/', 'unvote'),
    (r'^user/(?P<username>\w+)', 'summary'),
    (r'^allusers/', 'allusers'),
    (r'activity/(?P<assign>\d+)/(?P<username>\w+)', 'all_activity'),
    (r'^request_extension/(?P<assignment_id>\d+)', 'request_extension'),
    (r'^dashboard/(?P<username>\w+)', 'student_dashboard'),
    (r'^studentstats', 'student_stats'),
)
