from caesar.comments.models import Comment, Vote
from caesar.comments.forms import CommentForm

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
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
            comment.author = request.user
            comment.save()
            return redirect(comment.chunk)

@login_required
def delete(request):
    comment_id = request.GET['comment_id']
    comment = Comment.objects.get(pk=comment_id)
    comment.delete()
    return HttpResponse('deleted')

@login_required
def vote(request):
    comment_id = request.POST['comment_id']
    value = request.POST['value']
    comment = Comment.objects.get(pk=comment_id)
    vote = Vote(comment=comment, value=value, author=request.user)
    vote.save()
    return HttpResponse('success')
