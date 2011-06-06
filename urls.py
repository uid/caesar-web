from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^accounts/', include('accounts.urls')),
    (r'^chunks/', include('chunks.urls')),
    (r'^review/', include('review.urls')),

    (r'^api/', include('api.urls')),
)
