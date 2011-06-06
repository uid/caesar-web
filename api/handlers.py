from review.models import Comment
from chunks.models import Chunk
from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc
import re

class CommentHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    fields = ('id', 'text', 'chunk', 'start', 'end', 'type')
    model = Comment

    def read(self, request, comment_id=None):
        base = Comment.objects
        if comment_id:
            return base.get(pk=comment_id)
        else:
            return base.all()

    def create(self, request):
        data = request.data
        chunk = Chunk.objects.get(pk=data['chunk'])
        comment = self.model(
                text=data['text'], chunk=chunk,
                start=data['start'], end=data['end'], type=data['type'],
                author=request.user)
        comment.save()
        response = rc.CREATED
        response.write(str(comment.id))
        return response
