from django.conf.urls.defaults import *

urlpatterns = patterns('review.views',
    (r'^$', 'dashboard'),
    (r'^new_comment/', 'new_comment'),
    (r'^change_task/','change_task'),
    (r'^reply/', 'reply'),
    (r'^delete_comment/', 'delete_comment'),
    (r'^vote/', 'vote'),
    (r'^unvote/', 'unvote'),
)
