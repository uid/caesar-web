from django.conf.urls.defaults import *

urlpatterns = patterns('review.views',
    (r'^new/', 'new'),
    (r'^change_star/','change_star'),
    (r'^reply/', 'reply'),
    (r'^delete/', 'delete'),
    (r'^vote/', 'vote'),
    (r'^unvote/', 'unvote'),
)
