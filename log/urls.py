from django.conf.urls.defaults import *

urlpatterns = patterns('log.views',
    (r'^log/', 'log'),
)