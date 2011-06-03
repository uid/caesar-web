from comments.models import Comment, Vote, Star
from comments.forms import CommentForm, ReplyForm
from chunks.models import Chunk

from django.shortcuts import render, redirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def new(request):
    if request.method == 'GET':
        start = int(request.GET['start'])
        end = int(request.GET['end'])
        chunk_id = request.GET['chunk']
        form = CommentForm(initial={
            'start': start,
            'end': end,
            'chunk': chunk_id
        })
        chunk = Chunk.objects.get(pk=chunk_id)
        return render(request, 'comments/comment_form.html', {
            'form': form,
            'start': start,
            'end': end,
            'snippet': chunk.generate_snippet(start, end),
            'chunk': chunk,
        })  
    else:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.save()
            return redirect(comment.chunk)

@login_required
def reply(request):
    if request.method == 'GET':
        form = ReplyForm(initial={
            'parent': request.GET['parent']
        })
        return render(request, 'comments/reply_form.html', {'form': form,})
    else:
        form = ReplyForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            parent = Comment.objects.get(id=comment.parent.id)
            comment.chunk = parent.chunk
            comment.end = parent.end
            comment.start = parent.start 
            comment.save()
            return redirect(comment.chunk)

@login_required
def delete(request):
    comment_id = request.GET['comment_id']
    comment = Comment.objects.get(pk=comment_id)
    if comment.author == request.user:
        comment.delete()
    return HttpResponse('deleted')

@login_required
def vote(request):
    comment_id = request.POST['comment_id']
    value = request.POST['value']
    comment = Comment.objects.get(pk=comment_id)
    try:
        vote = Vote.objects.get(comment=comment, author=request.user)
        vote.value = value
    except Vote.DoesNotExist:
        vote = Vote(comment=comment, value=value, author=request.user)

    vote.save()
    return render(request, 'comments/comment_votes.html', {'comment': comment})

@login_required
def unvote(request):
    comment_id = request.POST['comment_id']
    comment = Comment.objects.get(pk=comment_id)
    Vote.objects.filter(comment=comment, author=request.user).delete()
    return render(request, 'comments/comment_votes.html', {'comment': comment})

@login_required
def change_star(request):
    if request.POST['value'] == "check":
        value = True
    else:
        value = False
    chunk_id = request.POST['chunk_id']
    chunk = Chunk.objects.get(pk=chunk_id)
    try:
        star = Star.objects.get(chunk=chunk, author=request.user)
        star.value = value
        star.save()
    except Star.DoesNotExist:
        star = Star(chunk=chunk, value=value, author=request.user)
        star.save()
        
    return render(request,'comments/change_star.html',{'star':star})
