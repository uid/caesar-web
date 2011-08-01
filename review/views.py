from review.models import Comment, Vote, Star 
from review.forms import CommentForm, ReplyForm
from review import app_settings
from chunks.models import Chunk, Assignment, Submission
from tasks.models import Task

from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required 
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from chunks.models import Chunk, Assignment
from tasks.models import Task
from tasks.routing import assign_tasks
from models import Comment, Vote, Star 
from forms import CommentForm, ReplyForm

@login_required
def dashboard(request):
    user = request.user
    new_task_count = 0
    for assignment in Assignment.objects.all():
        new_task_count += assign_tasks(assignment, user)
    
    active_tasks = user.get_profile().tasks \
        .select_related('chunk__file').exclude(status='C') \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    completed_tasks = user.get_profile().tasks \
        .select_related('chunk__file').filter(status='C') \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))
   
    return render(request, 'review/dashboard.html', {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'new_task_count': new_task_count,
    })

@staff_member_required
def stats(request):
    chunks = Chunk.objects.all()
    chunks_with_comments = \
            Chunk.objects.filter(comments__type='U') \
            .annotate(user_comment_count=Count('comments'))
    tasks = Task.objects.all()
    completed_tasks = Task.objects.filter(status='C')
    recent_comments = Comment.objects.filter(type='U').order_by('-created')[:10]
    return render(request, 'review/stats.html', {
        'chunks': chunks,
        'chunks_with_comments': chunks_with_comments,
        'tasks': tasks,
        'completed_tasks': completed_tasks,
        'recent_comments': recent_comments,
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
                task = Task.objects.get(
                    chunk=chunk_id, reviewer=user.get_profile())
                if task.status == 'N' or task.status == 'O':
                    task.mark_as('S')
            except Task.DoesNotExist:
                pass
            return render(request, 'review/comment.html', {
                'comment': comment
            })

@login_required
def reply(request):
    if request.method == 'GET':
        form = ReplyForm(initial={
            'parent': request.GET['parent']
        })
        return render(request, 'review/reply_form.html', {'form': form})
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
            return render(request, 'review/comment.html', {
                'comment': comment
            })

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

def summary(request):
    user = request.user
    #get all comments that the user wrote
    comments = Comment.objects.filter(author=user)
    chunk_stats = dict() #maps chunk and numbers of comments by the user
    for comment in comments:
        if not comment.chunk in chunk_stats:
            chunk_stats[comment.chunk] = 1
        else:
            chunk_stats[comment.chunk] += 1
    review_data = []
    for key in chunk_stats.keys():
        review_data.append((key, chunk_stats[key]))
    #get all the submissions that the user submitted
    submissions = Submission.objects.filter(author=user)
    
    return render(request, 'review/summary.html', {
        'review_data': review_data,
        'submissions': submissions,
    })
