from api.handlers import CommentHandler

from django.utils import simplejson
from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
from piston.utils import Mimer

auth = HttpBasicAuthentication(realm="Caesar")
ad = { 'authentication': auth }

# Workaround for django-piston bug in charset handling
Mimer.register(simplejson.loads, 
        ('application/json', 'application/json; charset=UTF-8',))

class CsrfExemptResource(Resource):
    def __init__(self, handler, authentication=None):
        super(CsrfExemptResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

comment_handler = CsrfExemptResource(CommentHandler, **ad)

urlpatterns = patterns('',
   (r'^comments/', comment_handler),
   (r'^comment/(?P<comment_id>\d+)/', comment_handler)
)
