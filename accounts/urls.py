from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'login/', 'accounts.views.login'),
    (r'logout/', 'django.contrib.auth.views.logout'),
    (r'register/', 'accounts.views.register'),
)
