from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^accounts/', include('caesar.accounts.urls')),
    (r'^chunks/', include('caesar.chunks.urls')),
    (r'^comments/', include('caesar.comments.urls')),

    (r'^api/', include('caesar.api.urls')),
)
