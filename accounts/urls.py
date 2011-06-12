from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'login/', 'django.contrib.auth.views.login', {
        'template_name': 'accounts/login.html',    
    }),
    (r'logout/', 'django.contrib.auth.views.logout'),
    (r'register/', 'accounts.views.register'),
)
