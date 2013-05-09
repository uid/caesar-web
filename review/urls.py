from django.conf.urls.defaults import *

urlpatterns = patterns('review.views',
    (r'^new_comment/', 'new_comment'),
    (r'^reply/', 'reply'),
    (r'^delete_comment/', 'delete_comment'),
    (r'^edit_comment/', 'edit_comment'),
    (r'^vote/', 'vote'),
    (r'^unvote/', 'unvote'),
    (r'activity/(?P<review_milestone_id>\d+)/(?P<username>\w+)', 'all_activity'),
    (r'^search', 'search'),
)
