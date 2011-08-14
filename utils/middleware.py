class ContentTypeMiddleware:
    """
    Workaround for a bug in django-piston
    """
    def process_request(self, request):
        if request.method in ('POST', 'PUT'):
            # dont break the multi-part headers !
            if not 'boundary=' in request.META['CONTENT_TYPE']:
                del request.META['CONTENT_TYPE']
