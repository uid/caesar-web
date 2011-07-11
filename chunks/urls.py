from django.conf.urls.defaults import *

urlpatterns = patterns('chunks.views',
    (r'view/(?P<chunk_id>\d+)', 'view_chunk'),
	(r'all/(?P<assign>(-|\w)+)/(?P<username>\w+)', 'view_all_chunks'),
)
