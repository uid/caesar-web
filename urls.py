from django.conf.urls.defaults import *
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^$', RedirectView.as_view(url='review/dashboard')),
    (r'^review/', include('review.urls')),
)

