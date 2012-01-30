from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'login/', 'django.contrib.auth.views.login', {
        'template_name': 'accounts/login.html',    
    }),
    (r'logout/', 'django.contrib.auth.views.logout'),
    (r'register/(?P<code>[0-9A-Za-z]+)', 'accounts.views.register'),
    (r'reputation_adj/', 'accounts.views.reputation_adjustment'),
    (r'register/', 'accounts.views.invalid_registration'),
    (r'^reset/$', 'django.contrib.auth.views.password_reset', 
                  {'template_name': 'accounts/reset.html'}),
    (r'^reset/done/$', 'django.contrib.auth.views.password_reset_done',
                      {'template_name': 'accounts/reset_done.html'}),
    (r'^reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 
            'django.contrib.auth.views.password_reset_confirm',
            {'template_name': 'accounts/reset_confirm.html'}),
    (r'^reset/complete/$', 'django.contrib.auth.views.password_reset_complete',
                           {'template_name': 'accounts/reset_complete.html'}), 
)
