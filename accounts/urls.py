from django.conf.urls.defaults import *
from django.views.generic import TemplateView
#from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    (r'login/', 'django.contrib.auth.views.login', {
        'template_name': 'accounts/login.html',
    }),
    (r'logout/', 'django.contrib.auth.views.logout'),
    (r'register/(?P<email>.+alum\.mit\.edu)/(?P<code>[0-9A-Fa-f]+$)', 'accounts.views.register'),
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
    (r'registration/$', 'accounts.views.registration_request'),
    (r'^registration/complete/$', TemplateView.as_view(template_name='accounts/registration_request_complete.html')),
    (r'^enroll/', 'accounts.views.edit_membership'),
    (r'bulk_add/', 'accounts.views.bulk_add'),
    (r'^user/(?P<username>\w+)/edit', 'accounts.views.edit_profile'),
    (r'^user/(?P<username>\w+)', 'accounts.views.view_profile'),
    (r'^request_extension/(?P<milestone_id>\d+)', 'accounts.views.request_extension'),
    (r'^allusers/', 'accounts.views.allusers'),
    (r'^manage/', 'accounts.views.manage'),
)
