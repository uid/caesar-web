from django.conf.urls.defaults import *
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^accounts/', include('accounts.urls')),
    (r'^chunks/', include('chunks.urls')),
    (r'^review/', include('review.urls')),

    (r'^api/', include('api.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)