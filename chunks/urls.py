from django.conf.urls.defaults import *

urlpatterns = patterns('chunks.views',
    (r'^view/(?P<chunk_id>\d+)', 'view_chunk'),
    (r'^submission/(?P<viewtype>(all|code))/(?P<submission_id>\d+)', 'view_all_chunks'),
    (r'^submission-for-milestone/(?P<viewtype>(all|code))/(?P<milestone_id>\d+)/(?P<username>\w+)', 'view_submission_for_milestone'),
    (r'^simulate/(?P<review_milestone_id>\d+)', 'simulate'),
    (r'^list_users/(?P<review_milestone_id>\d+)', 'list_users'),
    (r'^publish/', 'publish_code'),
    (r'^load_similar_comments/(?P<chunk_id>\d+)', 'load_similar_comments'),
)
