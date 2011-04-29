from api.handlers import CommentHandler

from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

auth = HttpBasicAuthentication(realm="Caesar")
ad = { 'authentication': auth }

comment_handler = Resource(CommentHandler, **ad)

urlpatterns = patterns('',
   (r'^comments/', comment_handler),
   (r'^comment/(?P<comment_id>\d+)/', comment_handler)
)
