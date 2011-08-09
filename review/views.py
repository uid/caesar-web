from django.db.models import Count, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required 
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from chunks.models import Chunk, Assignment, Submission
from tasks.models import Task
from tasks.routing import assign_tasks
from models import Comment, Vote, Star 
from forms import CommentForm, ReplyForm

from pygments import highlight
from pygments.lexers import JavaLexer
from pygments.formatters import HtmlFormatter

@login_required
def dashboard(request):
    user = request.user
    new_task_count = 0
    for assignment in Assignment.objects.all():
        new_task_count += assign_tasks(assignment, user)
    
    active_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission_assignment') \
        .exclude(status='C') \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    completed_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission__assignment') \
        .filter(status='C') \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))
   
    #get all the submissions that the user submitted
    submissions = user.submissions \
        .select_related('chunk__file__assignment') \
        .annotate(reviewer_count=Count('files__chunks__tasks', distinct=True),
                  last_modified = Max('files__chunks__comments__modified'))
    
    submission_data = []
    for submission in submissions:
        user_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U').count()
        static_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='S').count()
        submission_data.append((submission, submission.reviewer_count, submission.last_modified, 
                                  user_comments, static_comments))
    return render(request, 'review/dashboard.html', {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
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
            user = request.user
            chunk = comment.chunk
            try:
                task = Task.objects.get(
                    chunk=chunk, reviewer=user.get_profile())
                if task.status == 'N' or task.status == 'O':
                    task.mark_as('S')
            except Task.DoesNotExist:
                pass
            return render(request, 'review/comment.html', {
                'comment': comment,
                'chunk': chunk,
                'snippet': chunk.generate_snippet(comment.start, comment.end),
                'full_view': True,
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

def summary(request, username):
    participant = User.objects.get(username__exact=username)
    assignment_data = []
    #get all assignments
    assignments = Assignment.objects.all()
    for assignment in assignments: 
        #get all comments that the user wrote
        comments = Comment.objects.filter(author=participant).filter(chunk__file__submission__assignment = assignment).select_related('chunk')
        review_data = []
        for comment in comments:
            if comment.is_reply():
                #false means not a vote activity
                review_data.append(("reply-comment", comment, False, None))
            else:
                review_data.append(("new-comment", comment, False, None))
    
        votes = Vote.objects.filter(author=participant).filter(comment__chunk__file__submission__assignment = assignment).select_related('comment__chunk')
        for vote in votes:
            if vote.value == 1:
                #true means vote activity
                review_data.append(("vote-up", vote.comment, True, vote))
            elif vote.value == -1:
                review_data.append(("vote-down", vote.comment, True, vote))
        review_data = sorted(review_data, key=lambda element: element[1].modified, reverse = True)
        assignment_data.append((assignment, review_data))
    return render(request, 'review/summary.html', {
        'assignment_data': assignment_data,
        'participant': participant
    })
def activity(request, element_id, element_type):
    user = request.user
    vote = None
    comment = None
    chunk = None
    full_view = False
    highlight_comment = None
    if element_type == "vote":
        vote = Vote.objects.get(id__exact = element_id)
        comment = (vote.comment)
        chunk = vote.comment.chunk
        if vote.author == user:
            full_view = True
    elif element_type == "comment":
        comment = Comment.objects.get(id__exact = element_id)
        chunk = comment.chunk
        if comment.author == user:
            full_view = True
        highlight_comment = comment
    comments = [comment]
    if comment.is_reply():
        comments = Comment.objects.filter(thread_id = comment.thread_id)
    
    lexer = JavaLexer()
    formatter = HtmlFormatter(cssclass='syntax', nowrap=True)
    numbers, lines = zip(*chunk.lines)
    # highlight the code this way to correctly identify multi-line constructs
    # TODO implement a custom formatter to do this instead
    highlighted_lines = zip(numbers, 
            highlight(chunk.data, lexer, formatter).splitlines())
    
    return render(request, 'review/activity.html', {
        'chunk': chunk,
        'vote': vote,
        'highlight_comment': highlight_comment,
        'comments': comments,
        'highlighted_lines': highlighted_lines,
        'full_view': full_view,
        'activity_view': True,
        'user': user
    })


def allusers(request):
    participants = User.objects.all().exclude(username = 'checkstyle').select_related('profile')
    return render(request, 'review/allusers.html', {
        'participants': participants,
    })