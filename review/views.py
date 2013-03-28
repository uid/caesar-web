import json

from django.core import serializers
from django.db.models import Q, Count, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, Http404
from django.core.urlresolvers import reverse
from  django.core.exceptions import ObjectDoesNotExist

from chunks.models import Chunk, Assignment, Milestone, SubmitMilestone, ReviewMilestone, Submission, StaffMarker
from tasks.models import Task
from tasks.routing import assign_tasks
from models import Comment, Vote, Star
from review.forms import CommentForm, ReplyForm, EditCommentForm
from accounts.forms import UserProfileForm
from accounts.models import UserProfile, Extension
from simplewiki.models import Article

from pygments import highlight
from pygments.lexers import JavaLexer, SchemeLexer
from pygments.formatters import HtmlFormatter

from PIL import Image as PImage
from os.path import join as pjoin
from django.conf import settings

import datetime
import sys

@login_required
def dashboard(request):
    user = request.user
    new_task_count = 0
    open_assignments = False

    live_review_milestones = ReviewMilestone.objects.filter(assignment__is_live=True, assigned_date__lt=datetime.datetime.now(),\
         duedate__gt=datetime.datetime.now(), assignment__semester__members__user=user).all()

    for review_milestone in live_review_milestones:
        current_tasks = user.get_profile().tasks.filter(milestone=review_milestone)
        active_sub = Submission.objects.filter(author=user, milestone=review_milestone.submit_milestone)
        membership = Member.obects.filter(user=user, semester=review_milestone.assignment.semester)
        #do not give tasks to students who got extensions or already have tasks for this assignment
        #(TODO) refactor member.role to not be so arbitrary
        if (not current_tasks.count()) and (active_sub.count() or not 'student' in membership.role):
            open_assignments = True
            new_task_count += assign_tasks(review_milestone, user)

    old_completed_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission__milestone') \
        .filter(status='C') \
        .exclude(chunk__file__submission__milestone__assignment__semester__is_current_semester=True) \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    active_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission__milestone') \
        .exclude(status='C') \
        .exclude(status='U') \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    completed_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission__milestone') \
        .filter(status='C') \
        .filter(chunk__file__submission__milestone__assignment__semester__is_current_semester=True) \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    #get all the submissions that the user submitted
    submissions = Submission.objects.filter(author=user) \
        .filter(milestone__duedate__lt=datetime.datetime.now()) \
        .order_by('milestone__duedate')\
        .filter(milestone__assignment__semester__is_current_semester=True)\
        .select_related('chunk__file__assignment') \
        .annotate(last_modified=Max('files__chunks__comments__modified'))\
        .reverse()

    submission_data = []
    for submission in submissions:
        user_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U').count()
        static_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='S').count()
        reviewer_count = UserProfile.objects.filter(tasks__chunk__file__submission = submission).count()
        submission_data.append((submission, reviewer_count, submission.last_modified,
                                  user_comments, static_comments))

    #get all the submissions that the user submitted, in previous semesters
    old_submissions = Submission.objects.filter(author=user) \
        .filter(milestone__duedate__lt=datetime.datetime.now()) \
        .order_by('milestone__duedate')\
        .exclude(milestone__assignment__semester__is_current_semester=True)\
        .select_related('chunk__file__assignment') \
        .annotate(last_modified=Max('files__chunks__comments__modified'))\
        .reverse()

    old_submission_data = []
    for submission in old_submissions:
        user_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U').count()
        static_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='S').count()
        reviewer_count = UserProfile.objects.filter(tasks__chunk__file__submission = submission).count()
        old_submission_data.append((submission, reviewer_count, submission.last_modified,
                                  user_comments, static_comments))

    #find the current submissions
    current_milestones = Milestone.objects.filter(assignment__semester__members__user=user)\
        .filter(duedate__gt=datetime.datetime.now() - datetime.timedelta(minutes=30))\
        .filter(assigned_date__lt= datetime.datetime.now() - datetime.timedelta(minutes=30))\
        .order_by('duedate')

    current_milestone_data = []
    for milestone in current_milestones:
        try:
            user_extension = milestone.extensions.get(user=user)
            current_milestone_data.append((milestone, user_extension))
        except ObjectDoesNotExist:
            current_milestone_data.append((milestone, None))

    return render(request, 'review/dashboard.html', {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'old_completed_tasks': old_completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
        'old_submission_data': old_submission_data,
        'current_milestone_data': current_milestone_data,
        'open_assignments': open_assignments,
    })

@staff_member_required
def review_milestone_info(request, review_milestone_id):
    review_milestone = get_object_or_404(ReviewMilestone, pk=review_milestone_id)
    total_chunks = Chunk.objects.filter(file__submission__milestone=review_milestone.submit_milestone).count()
    alums_participating = User.objects.exclude(profile__role='S').exclude(profile__role='T')\
                                    .filter(comments__chunk__file__submission__milestone=review_milestone.submit_milestone)\
                                    .exclude(username='checkstyle').distinct().count()
    total_tasks = Task.objects.filter(milestone=review_milestone).count()
    assigned_chunks = Chunk.objects.filter(tasks__gt=0).filter(file__submission__milestone=review_milestone.submit_milestone).distinct().count()
    total_chunks_with_human = Chunk.objects.filter(comments__type='U').filter(file__submission__milestone=review_milestone.submit_milestone).distinct().count()
    total_comments = Comment.objects.filter(chunk__file__submission__milestone=review_milestone.submit_milestone).count()
    total_checkstyle = Comment.objects.filter(chunk__file__submission__milestone=review_milestone.submit_milestone).filter(type='S').count()
    total_staff_comments = Comment.objects.filter(chunk__file__submission__milestone=review_milestone.submit_milestone).filter(author__profile__role='T').count()
    total_student_comments = Comment.objects.filter(chunk__file__submission__milestone=review_milestone.submit_milestone).filter(author__profile__role='S').count()
    total_user_comments = Comment.objects.filter(chunk__file__submission__milestone=review_milestone.submit_milestone).filter(type='U').count()
    total_alum_comments = total_user_comments - total_staff_comments - total_student_comments
    zero_chunk_users = len(filter(lambda sub: len(sub.chunks()) == 0, review_milestone.submit_milestone.submissions.all()))

    return render(request, 'review/review_milestone_info.html', {
        'review_milestone': review_milestone,
        'total_chunks': total_chunks,
        'alums_participating': alums_participating,
        'total_tasks': total_tasks,
        'assigned_chunks': assigned_chunks,
        'total_chunks_with_human': total_chunks_with_human,
        'total_comments': total_comments,
        'total_checkstyle': total_checkstyle,
        'total_staff_comments': total_staff_comments,
        'total_student_comments': total_student_comments,
        'total_user_comments': total_user_comments,
        'total_alum_comments': total_alum_comments,
        'zero_chunk_users': zero_chunk_users,
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
                'file': chunk.file
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
def edit_comment(request):
    if request.method == 'GET':
        comment_id = request.GET['comment_id']
        comment = Comment.objects.get(pk=comment_id)
        start = comment.start
        end = comment.end
        form = EditCommentForm(initial={
             'text': comment.text,
             'comment_id': comment.id,
        })
        chunk = Chunk.objects.get(pk=comment.chunk.id)
        return render(request, 'review/edit_comment_form.html', {
            'form': form,
            'start': start,
            'end': end,
            'snippet': chunk.generate_snippet(start, end),
            'chunk': chunk,
            'comment_id': comment.id,
            'reply': comment.is_reply(),
        })
    else:
        form = EditCommentForm(request.POST)
        if form.is_valid():
            comment_id = form.cleaned_data['comment_id']
            comment = Comment.objects.get(id=comment_id)
            comment.text = form.cleaned_data['text']
            comment.edited = datetime.datetime.now()
            comment.save()
            chunk = comment.chunk
            return render(request, 'review/comment.html', {
                'comment': comment,
                'chunk': chunk,
                'snippet': chunk.generate_snippet(comment.start, comment.end),
                'full_view': True,
                'file': chunk.file,
            })

@login_required
def delete_comment(request):
    comment_id = request.GET['comment_id']
    comment = Comment.objects.get(pk=comment_id)
    if comment.author == request.user:
        # This will cascade and delete all replies as well
        comment.deleted = True
        comment.save()
    chunk = comment.chunk
    return render(request, 'review/comment.html', {
        'comment': comment,
        'chunk': chunk,
        'snippet': chunk.generate_snippet(comment.start, comment.end),
        'full_view': True,
        'file': chunk.file,
    })

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
        next_task = request.user.get_profile().tasks.exclude(status='C').exclude(status='U') \
                                              .order_by('created')[0:1].get()
        return redirect(next_task.chunk)
    except Task.DoesNotExist:
        return redirect('review.views.dashboard')

@login_required
def summary(request, username):
    try:
        participant = User.objects.get(username__exact=username)
    except:
        raise Http404
    review_milestone_data = []
    #get all submission milestones
    review_milestones = ReviewMilestone.objects.all().order_by('-assigned_date')
    for review_milestone in review_milestones:
        #get all comments that the user wrote
        comments = Comment.objects.filter(author=participant) \
                          .filter(chunk__file__submission__milestone= review_milestone.submit_milestone).select_related('chunk')
        review_data = []
        for comment in comments:
            if comment.is_reply():
                #false means not a vote activity
                review_data.append(("reply-comment", comment, comment.generate_snippet(), False, None))
            else:
                review_data.append(("new-comment", comment, comment.generate_snippet(), False, None))

        votes = Vote.objects.filter(author=participant) \
                    .filter(comment__chunk__file__submission__milestone = review_milestone.submit_milestone) \
                    .select_related('comment__chunk')
        for vote in votes:
            if vote.value == 1:
                #true means vote activity
                review_data.append(("vote-up", vote.comment, vote.comment.generate_snippet(), True, vote))
            elif vote.value == -1:
                review_data.append(("vote-down", vote.comment, vote.comment.generate_snippet(), True, vote))
        review_data = sorted(review_data, key=lambda element: element[1].modified, reverse = True)
        review_milestone_data.append((review_milestone, review_data))
    return render(request, 'review/summary.html', {
        'review_milestone_data': review_milestone_data,
        'participant': participant
    })

@login_required
def edit_profile(request, username):
    # can't edit if not current user
    if request.user.username != username:
        return redirect(reverse('review.views.summary', args=([username])))
    """Edit user profile."""
    profile = User.objects.get(username=username).profile
    photo = None
    img = None
    if profile.photo:
        photo = profile.photo.url
    else:
        photo = "http://placehold.it/180x144&text=Student"

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            if request.FILES:
                # resize and save image under same filename
                imfn = pjoin(settings.MEDIA_ROOT, profile.photo.name)
                im = PImage.open(imfn)
                im.thumbnail((180,180), PImage.ANTIALIAS)
                im.save(imfn, "PNG")
            return redirect(reverse('review.views.summary', args=([username])))
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'review/edit_profile.html', {
        'form': form,
        'photo': photo,
    })

@login_required
def allusers(request):
    participants = User.objects.all().exclude(username = 'checkstyle').select_related('profile').order_by('last_name')
    return render(request, 'review/allusers.html', {
        'participants': participants,
    })

@login_required
def all_activity(request, review_milestone_id, username):
    participant = User.objects.get(username__exact=username)
    if not participant:
        raise Http404
    user = request.user
    #get all assignments
    review_milestone = ReviewMilestone.objects.get(id__exact=review_milestone_id)
    if user.profile.is_student() and not review_milestone.assignment.is_current_semester():
        raise Http404
    #get all relevant chunks
    chunks = Chunk.objects \
        .filter(file__submission__milestone= review_milestone.submit_milestone) \
        .filter(Q(comments__author=participant) | Q(comments__votes__author=participant)) \
        .select_related('comments__votes', 'comments__author_profile')
    chunk_set = set()
    review_milestone_data = []

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

        staff_lines = StaffMarker.objects.filter(chunk=chunk).order_by('start_line', 'end_line')

        highlighted = zip(numbers,
                highlight(chunk.data, lexer, formatter).splitlines())

        highlighted_lines = []
        staff_line_index = 0
        for number, line in highlighted:
            if staff_line_index < len(staff_lines) and number >= staff_lines[staff_line_index].start_line and number <= staff_lines[staff_line_index].end_line:
                while staff_line_index < len(staff_lines) and number == staff_lines[staff_line_index].end_line:
                    staff_line_index += 1
                highlighted_lines.append((number, line, True))
            else:
                highlighted_lines.append((number, line, False))

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
        review_milestone_data.append((chunk, highlighted_lines, comment_data, chunk.file))

    return render(request, 'review/all_activity.html', {
        'review_milestone_data': review_milestone_data,
        'participant': participant,
        'activity_view': True,
        'full_view': True,
        'articles': [x for x in Article.objects.all() if not x == Article.get_root()],
    })

@login_required
def request_extension(request, milestone_id):
    user = request.user
    # User is going to request an extension
    if request.method == 'GET':
        current_milestone = Milestone.objects.get(id=milestone_id)
        # Make sure user got here legally
        user_duedate = user.profile.get_user_duedate(current_milestone)
        if datetime.datetime.now() > user_duedate + datetime.timedelta(minutes=30):
            return redirect('review.views.dashboard')

        total_extension_days_left = user.profile.extension_days()
        current_extension = (user_duedate - current_milestone.duedate).days

        late_days = 0
        if datetime.datetime.now() > current_milestone.duedate + datetime.timedelta(minutes=30):
            late_days = (datetime.datetime.now() - current_milestone.duedate + datetime.timedelta(minutes=30)).days + 1
       
        possible_extensions = range(late_days, min(total_extension_days_left+current_extension+1, current_milestone.max_extension+1))

        written_dates = []
        for day in range(possible_extensions[-1]+1):
            extension = day * datetime.timedelta(days=1)
            written_dates.append(current_milestone.duedate + extension)


        return render(request, 'review/extension_form.html', {
            'possible_extensions': possible_extensions,
            'current_extension': current_extension,
            'written_dates': written_dates,
            'total_extension_days': total_extension_days_left + current_extension
        })
    else: # user already requested an extension
        days = request.POST.get('dayselect', None)
        try:
            extension_days = int(days)
            current_milestone = Milestone.objects.get(id=milestone_id)
            user_duedate = user.profile.get_user_duedate(current_milestone)
            current_extension = (user_duedate - current_milestone.duedate).days
            total_extension_days_left = user.profile.extension_days()
            total_extension_days = total_extension_days_left + current_extension
            
            if extension_days > total_extension_days or extension_days < 0 or extension_days > current_milestone.max_extension:
                return redirect('review.views.dashboard')
            extension,created = Extension.objects.get_or_create(user=user, milestone=current_milestone)
            if extension_days == 0: # Don't keep extensions with 0 slack days
                extension.delete()
            else:
                extension.slack_used = extension_days
                extension.save()
            return redirect('review.views.dashboard')
        except ValueError:
            return redirect('review.views.dashboard')

#TODO: consolidate this with dashboard
@login_required
def student_dashboard(request, username):
    try:
        participant = User.objects.get(username=username)
    except:
        raise Http404
    user = request.user
    if user.profile.role != 'T':
        raise Http404
    new_task_count = 0

    old_completed_tasks = participant.get_profile().tasks \
        .select_related('chunk__file__submission__milestone') \
        .filter(status='C') \
        .exclude(chunk__file__submission__milestone__assignment__semester__is_current_semester=True) \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    active_tasks = participant.get_profile().tasks \
        .select_related('chunk__file__submission__milestone') \
        .exclude(status='C') \
        .exclude(status='U') \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    completed_tasks = participant.get_profile().tasks \
        .select_related('chunk__file__submission__milestone') \
        .filter(status='C') \
        .filter(chunk__file__submission__milestone__assignment__semester__is_current_semester=True) \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    #get all the submissions that the participant submitted
    submissions = Submission.objects.filter(author=participant) \
        .filter(milestone__duedate__lt=datetime.datetime.now()) \
        .order_by('milestone__duedate')\
        .filter(milestone__assignment__semester__is_current_semester=True)\
        .select_related('chunk__file__assignment') \
        .annotate(last_modified=Max('files__chunks__comments__modified'))\
        .reverse()

    submission_data = []
    for submission in submissions:
        user_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U').count()
        static_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='S').count()
        reviewer_count = UserProfile.objects.filter(tasks__chunk__file__submission = submission).count()
        submission_data.append((submission, reviewer_count, submission.last_modified,
                                  user_comments, static_comments))

    #get all the submissions that the user submitted, in previous semesters
    old_submissions = Submission.objects.filter(author=participant) \
        .filter(milestone__duedate__lt=datetime.datetime.now()) \
        .order_by('milestone__duedate')\
        .exclude(milestone__assignment__semester__is_current_semester=True)\
        .select_related('chunk__file__assignment') \
        .annotate(last_modified=Max('files__chunks__comments__modified'))\
        .reverse()

    old_submission_data = []
    for submission in old_submissions:
        user_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U').count()
        static_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='S').count()
        reviewer_count = UserProfile.objects.filter(tasks__chunk__file__submission = submission).count()
        old_submission_data.append((submission, reviewer_count, submission.last_modified,
                                  user_comments, static_comments))

    #find the current submissions
    current_milestones = Milestone.objects.filter(assignment__semester__members__user=participant)\
        .filter(duedate__gt=datetime.datetime.now() - datetime.timedelta(minutes=30))\
        .filter(assigned_date__lt= datetime.datetime.now() - datetime.timedelta(minutes=30))\
        .order_by('duedate')

    current_milestone_data = []
    for milestone in current_milestones:
        try:
            user_extension = milestone.extensions.get(user=user)
            current_milestone_data.append((milestone, user_extension))
        except ObjectDoesNotExist:
            current_milestone_data.append((milestone, None))

    return render(request, 'review/student_dashboard.html', {
        'participant': participant,
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'old_completed_tasks': old_completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
        'old_submission_data': old_submission_data,
        'current_milestone_data': current_milestone_data,
    })

@staff_member_required
def manage(request):
    return render(request, 'review/manage.html', {
    })
@staff_member_required
def cancel_assignment(request):
    if request.method == 'POST':
        assignments = request.POST.get('assignment', None)
        if assignments == "all":
            started_tasks = Task.objects.filter(status='S')
            started = 0
            for task in started_tasks:
                task.mark_as('C')
                started += 1
            unfinished_tasks = Task.objects.exclude(status='C').exclude(status='U')
            total = 0
            for task in unfinished_tasks:
                total += 1
                task.mark_as('U')
            response_json = json.dumps({
                'total': total,
            })
            return HttpResponse(response_json, mimetype='application/javascript')
    return render(request, 'review/manage.html', {
    })
@login_required
def more_work(request):
    if request.method == 'POST':
        user = request.user
        new_task_count = 0
        current_tasks = user.get_profile().tasks.exclude(status='C').exclude(status='U')
        total = 0
        if not current_tasks.count():
            live_review_milestones = ReviewMilestone.objects.filter(assignment__is_live=True, assigned_date__lt=datetime.datetime.now(),\
                duedate__gt=datetime.datetime.now(), assignment__semester__members_user=user).all()

            for milestone in live_review_milestones:
                current_tasks = user.get_profile().tasks.filter(milestone=milestone)
                active_sub = Submission.objects.filter(name=user.username, milestone=milestone.reviewmilestone.submit_milestone)
                #do not give tasks to students who got extensions or already have tasks for this assignment
                if (not current_tasks.count()) and active_sub.count():
                    open_assignments = True
                    total += assign_tasks(milestone, user, max_tasks=2, assign_more=True)
                    
            active_tasks = user.get_profile().tasks \
                .select_related('chunk__file__submission__milestone__assignment') \
                .exclude(status='C') \
                .exclude(status='U') \
                .annotate(comment_count=Count('chunk__comments', distinct=True),
                          reviewer_count=Count('chunk__tasks', distinct=True))
            one = active_tasks.all()[0]
            two = active_tasks.all()[1]
            response_json = json.dumps({
                'total': total,
                'one': {"task_chunk_name": one.chunk.name, \
                                 "task_comment_count": one.comment_count,\
                                 "task_reviewer_count": one.reviewer_count, \
                                 "task_chunk_generate_snippet": one.chunk.generate_snippet(),\
                                 "task_id": one.id,\
                                 "task_chunk_id": one.chunk.id},
                'two': {"task_chunk_name": two.chunk.name, \
                                 "task_comment_count": two.comment_count,\
                                 "task_reviewer_count": two.reviewer_count, \
                                 "task_chunk_generate_snippet": two.chunk.generate_snippet(),\
                                 "task_id": two.id,\
                                 "task_chunk_id": two.chunk.id},
            })
            return HttpResponse(response_json, mimetype='application/javascript')
    return render(request, 'review/manage.html', {
    })

def view_helper(comments):
    review_data = []
    for comment in comments:
        if comment.is_reply():
            #false means not a vote activity
            review_data.append(("reply-comment", comment, comment.generate_snippet(), False, None))
        else:
            review_data.append(("new-comment", comment, comment.generate_snippet(), False, None))
    review_data = sorted(review_data, key=lambda element: element[1].modified, reverse = True)
    return review_data

@login_required
def search(request):
    if request.method == 'POST':
        querystring = request.POST['value'].strip()
        if querystring:
            comments = Comment.objects.filter(chunk__file__submission__milestone__assignment__semester__is_current_semester=True,
                                              text__icontains = querystring)
            review_data = view_helper(comments[:15])
            return render(request, 'review/search.html', {
                                   'review_data': review_data,
                                   'query': querystring,
                                   'num_results': len(comments),
            })
    return render(request, 'review/search.html', {
                               'review_data': [],
                           })
