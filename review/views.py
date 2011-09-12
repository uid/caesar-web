import json

from django.core import serializers
from django.db.models import Q, Count, Max
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
from review.forms import CommentForm, ReplyForm
from accounts.models import UserProfile

from pygments import highlight
from pygments.lexers import JavaLexer
from pygments.formatters import HtmlFormatter

import datetime
import sys

@login_required
def dashboard(request):
    user = request.user
    new_task_count = 0
    for assignment in Assignment.objects.filter(code_review_end_date__gt=datetime.datetime.now()):
        active_sub = Submission.objects.filter(name=user.username).filter(assignment=assignment)
        #do not give tasks to students who got extensions
        if len(active_sub) == 0 or active_sub[0].duedate < datetime.datetime.now():
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
    submissions = Submission.objects.filter(name=user.username) \
        .filter(duedate__lt=datetime.datetime.now()) \
        .order_by('files__chunks__comments__modified') \
        .select_related('chunk__file__assignment') \
        .annotate(last_modified=Max('files__chunks__comments__modified'))
    
    submission_data = []
    for submission in submissions:
        user_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U').count()
        static_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='S').count()
        reviewer_count = UserProfile.objects.filter(tasks__chunk__file__submission = submission).count()
        submission_data.append((submission, reviewer_count, submission.last_modified, 
                                  user_comments, static_comments))
    
    #find the current assignments
    current_submissions = Submission.objects.filter(name=user.username).filter(duedate__gt=datetime.datetime.now()).order_by('duedate')
    
    return render(request, 'review/dashboard.html', {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
        'current_submissions': current_submissions,
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
            chunk = parent.chunk
            comment.chunk = chunk
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
                'comment': comment,
                'chunk': chunk,
                'snippet': chunk.generate_snippet(comment.start, comment.end),
                'full_view': True,
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
    response_json = json.dumps({
        'comment_id': comment_id,
        'upvote_count': comment.upvote_count,
        'downvote_count': comment.downvote_count,
    })
    return HttpResponse(response_json, mimetype='application/javascript')

@login_required
def unvote(request):
    comment_id = request.POST['comment_id']
    Vote.objects.filter(comment=comment_id, author=request.user).delete()
    # need to make sure to load the comment after deleting the vote to make sure
    # the vote counts are correct
    comment = Comment.objects.get(pk=comment_id)
    sys.stderr.write("\ncomment: " + comment_id)
    response_json = json.dumps({
        'comment_id': comment_id,
        'upvote_count': comment.upvote_count,
        'downvote_count': comment.downvote_count,
    })
    return HttpResponse(response_json, mimetype='application/javascript')

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

@login_required
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
                review_data.append(("reply-comment", comment, comment.generate_snippet(), False, None))
            else:
                review_data.append(("new-comment", comment, comment.generate_snippet(), False, None))
    
        votes = Vote.objects.filter(author=participant) \
                    .filter(comment__chunk__file__submission__assignment = assignment) \
                    .select_related('comment__chunk')
        for vote in votes:
            if vote.value == 1:
                #true means vote activity
                review_data.append(("vote-up", vote.comment, vote.comment.generate_snippet(), True, vote))
            elif vote.value == -1:
                review_data.append(("vote-down", vote.comment, vote.comment.generate_snippet(), True, vote))
        review_data = sorted(review_data, key=lambda element: element[1].modified, reverse = True)
        assignment_data.append((assignment, review_data))
    return render(request, 'review/summary.html', {
        'assignment_data': assignment_data,
        'participant': participant
    })

@login_required
def allusers(request):
    participants = User.objects.all().exclude(username = 'checkstyle').select_related('profile')
    return render(request, 'review/allusers.html', {
        'participants': participants,
    })

@login_required
def all_activity(request, assign, username):
    participant = User.objects.get(username__exact=username)
    user = request.user
    #get all assignments
    assignment = Assignment.objects.get(id__exact=assign)
    #get all relevant chunks
    chunks = Chunk.objects \
        .filter(file__submission__assignment = assignment) \
        .filter(Q(comments__author=participant) | Q(comments__votes__author=participant)) \
        .select_related('comments__votes', 'comments__author_profile')
    chunk_set = set()
    assignment_data = []

    lexer = JavaLexer()
    formatter = HtmlFormatter(cssclass='syntax', nowrap=True)   
    for chunk in chunks:
        if chunk in chunk_set:
            continue
        else:
            chunk_set.add(chunk)
        participant_votes = dict((vote.comment.id, vote.value) \
                for vote in participant.votes.filter(comment__chunk=chunk.id))
        numbers, lines = zip(*chunk.lines)
        highlighted_lines = zip(numbers, 
                highlight(chunk.data, lexer, formatter).splitlines())
        comments = chunk.comments.select_related('votes', 'author__profile')
        highlighted_comments = []
        highlighted_votes = []
        for comment in comments:
            if comment.id in participant_votes:
                highlighted_votes.append(participant_votes[comment.id])
            else: 
                highlighted_votes.append(None)
            if comment.author == participant:
                highlighted_comments.append(comment)
            else:
                highlighted_comments.append(None)
        comment_data = zip(comments, highlighted_comments, highlighted_votes)
        assignment_data.append((chunk, highlighted_lines, comment_data))

    return render(request, 'review/all_activity.html', {
        'assignment_data': assignment_data,
        'participant': participant,
        'activity_view': True,
        'full_view': False
    })
@login_required
def request_extension(request, assignment_id):
    user = request.user
    if request.method == 'GET':
        current_assignment = Assignment.objects.get(id=assignment_id)
        submission = Submission.objects.get(assignment=current_assignment, author=user)
        extension = user.profile.extension_days
        extended_days = (submission.duedate - current_assignment.duedate).days
        late_days = 0
        if datetime.datetime.now() > current_assignment.duedate:
            late_days = (datetime.datetime.now() - current_assignment.duedate).days + 1
        days = range(late_days, min(extension+extended_days+1, current_assignment.max_extension+1))
        written_days = []
        for day in range(days[-1]+1):
            written_days.append(current_assignment.duedate + datetime.timedelta(days=day))
        return render(request, 'review/extension_form.html', {
            'days': days,
            'current_day': extended_days,
            'written_days': written_days,
            'total_days': user.profile.extension_days + extended_days
        })  
    else:
        days = request.POST.get('dayselect', None)
        try:
            extension = int(days)
            total_left = user.profile.extension_days
            current_assignment = Assignment.objects.get(id=assignment_id)
            submission = Submission.objects.get(assignment=current_assignment, author=user)
            extended_days = (submission.duedate - current_assignment.duedate).days
            total_days = total_left + extended_days
            if extension > total_days or extension < 0 or extension > current_assignment.max_extension:
                return redirect('review.views.dashboard')
            user.profile.extension_days = total_days - extension
            user.profile.save()
            submission.duedate = current_assignment.duedate+datetime.timedelta(days=extension)
            submission.save()
            return redirect('review.views.dashboard')
        except ValueError:
            return redirect('review.views.dashboard')
