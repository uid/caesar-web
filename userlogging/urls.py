from django.conf.urls.defaults import *

urlpatterns = patterns('userlogging.views',
    (r'^log_comment_search/', 'log_comment_search'),
)