from caesar.comments.models import Comment
from caesar.comments.forms import CommentForm

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponse

def new(request):
    if request.method == 'GET':
        form = CommentForm(initial={
            'start': request.GET['start'],
            'end': request.GET['end'],
            'chunk': request.GET['chunk']
        })
        return render_to_response('comments/comment_form.html', {
            'form': form,
        }, context_instance=RequestContext(request))   
    else:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            # FIXME hardcoded to masont right now
            comment.author = User.objects.get(pk=1)
            comment.save()
            return redirect(comment.chunk)

def delete(request):
    comment_id = request.GET['comment_id']
    comment = Comment.objects.get(pk=comment_id)
    comment.delete()
    return HttpResponse('deleted')
