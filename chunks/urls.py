from django.conf.urls.defaults import *

urlpatterns = patterns('caesar.chunks.views',
    (r'view/(?P<chunk_id>\d+)', 'view_chunk'),
)
