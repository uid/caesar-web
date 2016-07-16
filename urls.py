from django.conf.urls.defaults import *
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^$', RedirectView.as_view(url='dashboard/')),

    (r'^accounts/', include('accounts.urls')),
    (r'accounts/$', 'django.contrib.auth.views.login', {
        'template_name': 'accounts/login.html',    
    }),
    (r'^chunks/', include('chunks.urls')),
    (r'^review/', include('review.urls')),
    (r'^dashboard/', include('dashboard.urls')),
    (r'^tasks/', include('tasks.urls')),
    (r'^log/', include('log.urls')),

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

