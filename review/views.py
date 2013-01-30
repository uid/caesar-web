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

from chunks.models import Chunk, Assignment, Submission, StaffMarker
from tasks.models import Task
from tasks.routing import assign_tasks
from models import Comment, Vote, Star
from review.forms import CommentForm, ReplyForm, EditCommentForm
from accounts.forms import UserProfileForm
from accounts.models import UserProfile
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

    #todo(mglidden): DELETE
    if user.profile.tasks.count() == 0:
      new_task_count += 3
      open_assignments = True
      chunk_ids = [1, 2, 3]
      for chunk_id in chunk_ids:
        t = Task(reviewer_id=user.profile.id, chunk_id=chunk_id)
        t.save()

    assignments = []
    for membership in user.membership.all():
      assignments.extend(filter(lambda assignment: assignment.is_live, membership.semester.assignments.all()))

    for assignment in assignments:
        active_sub = Submission.objects.filter(name=user.username).filter(assignment=assignment)
        #do not give tasks to students who got extensions
        if len(active_sub) == 0 or active_sub[0].duedate + datetime.timedelta(minutes=30) < datetime.datetime.now():
            open_assignments = True
            new_task_count += assign_tasks(assignment, user)

    old_completed_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission__assignment') \
        .filter(status='C') \
        .exclude(chunk__file__submission__assignment__semester__is_current_semester=True) \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))


    active_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission_assignment') \
        .exclude(status='C') \
        .exclude(status='U') \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    completed_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission__assignment') \
        .filter(status='C') \
        .filter(chunk__file__submission__assignment__semester__is_current_semester=True) \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    #get all the submissions that the user submitted, in the current semester
    submissions = Submission.objects.filter(name=user.username) \
        .filter(duedate__lt=datetime.datetime.now()-datetime.timedelta(minutes=30)) \
        .order_by('duedate')\
        .filter(assignment__semester__is_current_semester=True) \
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

    #get all the submissions that the user submitted, in previous semester
    old_submissions = Submission.objects.filter(name=user.username) \
        .filter(duedate__lt=datetime.datetime.now()) \
        .order_by('duedate') \
        .exclude(assignment__semester__is_current_semester=False) \
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

    #find the current assignments
    current_submissions = Submission.objects.filter(name=user.username)\
        .filter(duedate__gt=datetime.datetime.now() - datetime.timedelta(minutes=30))\
        .order_by('duedate')

    return render(request, 'review/dashboard.html', {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'old_completed_tasks': old_completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
        'old_submission_data': old_submission_data,
        'current_submissions': current_submissions,
        'open_assignments': open_assignments,
    })

@staff_member_required
def student_stats(request):
    assignments = Assignment.objects.all().order_by('duedate').reverse()[0:5]
    total_students = User.objects.filter(profile__role='S').count()
    total_alum = User.objects.exclude(profile__role='S').exclude(profile__role='T').count()
    all_alums = User.objects.exclude(profile__role='S').exclude(profile__role='T')
    total_staff = User.objects.filter(profile__role='T').count()

    assignment_data = []
    for assignment in assignments:
        total_chunks = Chunk.objects.filter(file__submission__assignment=assignment).count()
        all_alums = User.objects.exclude(profile__role='S').exclude(profile__role='T').filter(comments__chunk__file__submission__assignment=assignment).exclude(username='checkstyle').distinct()
        alums_participating = all_alums.count()
        total_extension = 0; one_day_extension = 0; half_day_extension = 0; two_day_extension = 0; three_day_extension = 0
        if (assignment.duedate):
          total_extension = Submission.objects.filter(duedate__gt = assignment.duedate).filter(assignment=assignment).count()
          one_day_extension = Submission.objects.filter(duedate = assignment.duedate + datetime.timedelta(days=1)).count()
          half_day_extension = Submission.objects.filter(duedate = assignment.duedate + datetime.timedelta(hours=12)).count()
          one_day_extension = max(one_day_extension, half_day_extension)
          two_day_extension = Submission.objects.filter(duedate = assignment.duedate + datetime.timedelta(days=2)).count()
          three_day_extension = Submission.objects.filter(duedate = assignment.duedate + datetime.timedelta(days=3)).count()
        total_tasks = Task.objects.filter(chunk__file__submission__assignment=assignment).count()
        assigned_chunks = Chunk.objects.filter(tasks__gt=0).filter(file__submission__assignment=assignment).distinct().count()
        total_chunks_with_human = Chunk.objects.filter(comments__type='U').filter(file__submission__assignment=assignment).distinct().count()
        total_comments = Comment.objects.filter(chunk__file__submission__assignment=assignment).count()
        total_checkstyle = Comment.objects.filter(chunk__file__submission__assignment=assignment).filter(type='S').count()
        total_staff_comments = Comment.objects.filter(chunk__file__submission__assignment=assignment).filter(author__profile__role='T').count()
        total_student_comments = Comment.objects.filter(chunk__file__submission__assignment=assignment).filter(author__profile__role='S').count()
        total_user_comments = Comment.objects.filter(chunk__file__submission__assignment=assignment).filter(type='U').count()
        total_alum_comments = total_user_comments - total_staff_comments - total_student_comments
        zero_chunk_users = len(filter(lambda sub: len(sub.files.all()) != 0 and len(sub.chunks()) == 0, assignment.submissions.all()))

        assignment_data.append( (assignment, total_chunks, alums_participating, total_extension, one_day_extension, two_day_extension, three_day_extension, total_tasks, assigned_chunks, total_chunks_with_human, total_comments, total_checkstyle, total_alum_comments, total_staff_comments, total_student_comments, total_user_comments, zero_chunk_users) )
    return render(request, 'review/studentstats.html', {
        'assignment_data': assignment_data,
        'total_students': total_students,
        'total_alums': total_alum,
        'total_staff': total_staff,
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
    participant = User.objects.get(username__exact=username)
    if not participant:
        raise Http404
    assignment_data = []
    #get all assignments
    assignments = Assignment.objects.all().order_by('created').reverse()
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
def all_activity(request, assign, username):
    participant = User.objects.get(username__exact=username)
    if not participant:
        raise Http404
    user = request.user
    #get all assignments
    assignment = Assignment.objects.get(id__exact=assign)
    if user.profile.is_student() and not assignment.is_current_semester():
        raise Http404
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
        assignment_data.append((chunk, highlighted_lines, comment_data, chunk.file))

    return render(request, 'review/all_activity.html', {
        'assignment_data': assignment_data,
        'participant': participant,
        'activity_view': True,
        'full_view': True,
        'articles': [x for x in Article.objects.all() if not x == Article.get_root()],
    })
@login_required
def request_extension(request, assignment_id):
    user = request.user
    # User is going to request an extension
    if request.method == 'GET':
        current_assignment = Assignment.objects.get(id=assignment_id)
        submission = Submission.objects.get(assignment=current_assignment, author=user)
        # Make sure user got here legally
        if datetime.datetime.now() >  submission.duedate + datetime.timedelta(minutes=30):
            return redirect('review.views.dashboard')

        extension = user.profile.extension_days()
        extended_days = (submission.duedate - current_assignment.duedate).days

        # Number of late days the student would use
        late_days = 0
        if datetime.datetime.now() > current_assignment.duedate + datetime.timedelta(minutes=30):
            late_days = (datetime.datetime.now() - current_assignment.duedate + datetime.timedelta(minutes=30)).days + 1

        days = range(late_days, min(extension+extended_days+1, current_assignment.max_extension+1))
        written_days = []
        for day in range(days[-1]+1):
            written_days.append(current_assignment.duedate + datetime.timedelta(days=day))

        if current_assignment.multiplier == 2: #beta submission
            if (submission.duedate - current_assignment.duedate).seconds/3600 == 12: #has extension
                extended_days = 1
            late_days = 0
            if datetime.datetime.now() > current_assignment.duedate + datetime.timedelta(minutes=30):
                late_days = 1
            days = range(late_days, min(extension+extended_days+1, current_assignment.max_extension+1))
            written_days = []
            for day in range(days[-1]+1):
                hours = day * 12
                written_days.append(current_assignment.duedate + datetime.timedelta(hours=hours))
        return render(request, 'review/extension_form.html', {
            'days': days,
            'current_day': extended_days,
            'written_days': written_days,
            'total_days': user.profile.extension_days + extended_days
        })
    else: # user already requested an extension
        days = request.POST.get('dayselect', None)
        try:
            extension_days = int(days)
            total_left = user.profile.extension_days()
            current_assignment = Assignment.objects.get(id=assignment_id)
            submission = Submission.objects.get(assignment=current_assignment, author=user)
            extended_days = (submission.duedate - current_assignment.duedate).days
            if (submission.duedate - current_assignment.duedate).seconds/3600 == 12:
                extended_days = 1
            total_days = total_left + extended_days
            if extension_days > total_days or extension_days < 0 or extension_days > current_assignment.max_extension:
                return redirect('review.views.dashboard')
            extension = Extension(slack_used=extension_days, user=user, assignment=current_assignment)
            extension.save()
            #user.profile.extension_days = total_days - extension
            #user.profile.save()
            submission.duedate = current_assignment.duedate + datetime.timedelta(days=extension_days)
            if current_assignment.multiplier == 2: #beta submission
                hours = extension * 12
                submission.duedate = current_assignment.duedate + datetime.timedelta(hours=hours)
            submission.save()
            return redirect('review.views.dashboard')
        except ValueError:
            return redirect('review.views.dashboard')

@login_required
def student_dashboard(request, username):
    participant = User.objects.get(username=username)
    user = request.user
    if user.profile.role != 'T':
        raise Http404
    new_task_count = 0

    # for assignment in Assignment.objects.filter(code_review_end_date__gt=datetime.datetime.now()):
    #     active_sub = Submission.objects.filter(name=participant.username).filter(assignment=assignment)
    #     #do not give tasks to students who got extensions
    #     if len(active_sub) == 0 or active_sub[0].duedate < datetime.datetime.now():
    #         new_task_count += assign_tasks(assignment, participant)
    old_completed_tasks = participant.get_profile().tasks \
        .select_related('chunk__file__submission__assignment') \
        .filter(status='C') \
        .exclude(chunk__file__submission__assignment__semester__is_current_semester=True) \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    active_tasks = participant.get_profile().tasks \
        .select_related('chunk__file__submission_assignment') \
        .exclude(status='C') \
        .exclude(status='U') \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    completed_tasks = participant.get_profile().tasks \
        .select_related('chunk__file__submission__assignment') \
        .filter(status='C') \
        .filter(chunk__file__submission__assignment__semester__is_current_semester=True) \
        .annotate(comment_count=Count('chunk__comments', distinct=True),
                  reviewer_count=Count('chunk__tasks', distinct=True))

    #get all the submissions that the participant submitted
    submissions = Submission.objects.filter(name=participant.username) \
        .filter(duedate__lt=datetime.datetime.now()) \
        .order_by('duedate')\
        .filter(assignment__semester__is_current_semester=True)\
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
    #get all the submissions that the user submitted, in the current semester
    old_submissions = Submission.objects.filter(name=participant.username) \
        .filter(duedate__lt=datetime.datetime.now()) \
        .order_by('duedate')\
        .exclude(assignment__semester__is_current_semester=True)\
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

    #find the current assignments
    current_submissions = Submission.objects.filter(name=participant.username).filter(duedate__gt=datetime.datetime.now()).order_by('duedate')

    return render(request, 'review/student_dashboard.html', {
        'participant': participant,
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'old_completed_tasks': old_completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
        'old_submission_data': old_submission_data,
        'current_submissions': current_submissions,
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
            for assignment in Assignment.objects.filter(code_review_end_date__gt=datetime.datetime.now(), is_live=True):
                active_sub = Submission.objects.filter(name=user.username).filter(assignment=assignment)
                #do not give tasks to students who got extensions
                if len(active_sub) == 0 or active_sub[0].duedate + datetime.timedelta(minutes=30) < datetime.datetime.now():
                    total += assign_tasks(assignment, user, max_tasks=2, assign_more=True)
            active_tasks = user.get_profile().tasks \
                .select_related('chunk__file__submission_assignment') \
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
            comments = Comment.objects.filter(chunk__file__submission__assignment__semester__is_current_semester=True,
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
