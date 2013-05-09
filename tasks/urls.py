from django.conf.urls.defaults import *

urlpatterns = patterns('tasks.views',
    (r'^more_work', 'more_work'),
    (r'^cancel_assignment', 'cancel_assignment'),
    (r'^review_milestone_info/(?P<review_milestone_id>\d+)', 'review_milestone_info'),
    (r'^change_task/', 'change_task'),
    (r'^stats/', 'stats'),
)
