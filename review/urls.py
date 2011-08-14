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
    (r'activity/(?P<element_type>(vote|comment))/(?P<element_id>\w+)', 'activity'),
    (r'activity/(?P<assign>\d+)/(?P<username>\w+)', 'all_activity')
)
