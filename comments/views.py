from caesar.comments.models import Comment
from caesar.comments.forms import CommentForm

from django.shortcuts import render_to_response
from django.template import RequestContext

def new_comment(request):
    if request.method == 'GET':
        form = CommentForm()
        return render_to_response('comments/comment_form.html', {
            'form': form,
        }, context_instance=RequestContext(request))   
    else:
        form = CommentForm(request.POST)


    
