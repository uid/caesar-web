from review.models import Comment, Vote, Star, Task
from review.forms import CommentForm, ReplyForm
from review import app_settings
from chunks.models import Chunk, Assignment

from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def dashboard(request):
    user = request.user
    assignment = Assignment.objects.get(pk=1)
    
    new_task_count = Task.objects.assign_tasks(assignment, user)
    
    active_tasks = user.get_profile().tasks \
        .select_related('chunk').exclude(status='C')
    completed_tasks = user.get_profile().tasks \
        .select_related('chunk').filter(status='C')
    return render(request, 'review/dashboard.html', {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'new_task_count': new_task_count,
    })

@login_required
def new_comment(request):
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
        return render(request, 'review/comment_form.html', {
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
            chunk_id = comment.chunk
            user = request.user
            try:
                task = Task.objects.get(chunk=chunk_id,
                        reviewer=user.get_profile())
                if task.status == 'N' or task.status == 'O':
                    task.mark_as('S')
            except Task.DoesNotExist:
                pass
            return redirect(comment.chunk)

@login_required
def reply(request):
    if request.method == 'GET':
        form = ReplyForm(initial={
            'parent': request.GET['parent']
        })
        return render(request, 'review/reply_form.html', {'form': form,})
    else:
        form = ReplyForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            parent = Comment.objects.get(id=comment.parent_id)
            comment.chunk = parent.chunk
            comment.end = parent.end
            comment.start = parent.start 
            if parent.is_reply():
                # strictly single threads for discussion
                comment.parent = parent.parent
            comment.save()
            try:
                task = Task.objects.get(chunk=comment.chunk,
                        reviewer=request.user.get_profile())
                if task.status == 'N' or task.status == 'O':
                    task.mark_as('S')
            except Task.DoesNotExist:
                pass
            return redirect(comment.chunk)

@login_required
def delete_comment(request):
    comment_id = request.GET['comment_id']
    comment = Comment.objects.get(pk=comment_id)
    if comment.author == request.user:
        # This will cascade and delete all replies as well
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
    # Reload the comment to make sure vote counts are up to date
    comment = Comment.objects.get(pk=comment_id)
    try:
        task = Task.objects.get(chunk=comment.chunk,
                reviewer=request.user.get_profile())
        if task.status == 'N' or task.status == 'O':
            task.mark_as('S')
    except Task.DoesNotExist:
        pass
    return render(request, 'review/comment_votes.html', {'comment': comment})

@login_required
def unvote(request):
    comment_id = request.POST['comment_id']
    Vote.objects.filter(comment=comment_id, author=request.user).delete()
    # need to make sure to load the comment after deleting the vote to make sure
    # the vote counts are correct
    comment = Comment.objects.get(pk=comment_id)
    return render(request, 'review/comment_votes.html', {'comment': comment})

@login_required
def change_task(request):
    task_id = request.REQUEST['task_id']
    status = request.REQUEST['status']
    task = get_object_or_404(Task, pk=task_id)
    task.mark_as(status)
    try:
        next_task = request.user.get_profile().tasks.exclude(status='C') \
                                              .order_by('created')[0:1].get()
        return redirect(next_task.chunk)
    except Task.DoesNotExist:
        return redirect('review.views.dashboard')

