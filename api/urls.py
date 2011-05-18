from api.handlers import CommentHandler

from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

auth = HttpBasicAuthentication(realm="Caesar")
ad = { 'authentication': auth }

class CsrfExemptResource(Resource):
    def __init__(self, handler, authentication=None):
        super(CsrfExemptResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

comment_handler = CsrfExemptResource(CommentHandler, **ad)

urlpatterns = patterns('',
   (r'^comments/', comment_handler),
   (r'^comment/(?P<comment_id>\d+)/', comment_handler)
)
