from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'login/', 'caesar.accounts.views.login'),
    (r'logout/', 'django.contrib.auth.views.logout')
)
