from django.core import serializers
from django.db.models import Q, Count, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib import auth

from review.models import *
from review.forms import *
from review.old_routing import assign_tasks
from limit_registration import check_email, send_email, verify_token

from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter

import datetime
import sys
import logging
import json
import re


@login_required
def dashboard(request):
    user = request.user

    # assign new reviewing tasks to this user
    new_task_count = 0
    allow_requesting_more_tasks = False
    live_review_milestones = ReviewMilestone.objects.filter(assigned_date__lt=datetime.datetime.now(),\
         duedate__gt=datetime.datetime.now(), assignment__semester__members__user=user).all()
    for review_milestone in live_review_milestones:
        #logging.debug("live reviewing milestone: " + review_milestone)
        current_tasks = user.tasks.filter(milestone=review_milestone)
        active_sub = Submission.objects.filter(authors=user, milestone=review_milestone.submit_milestone)
        try:
            membership = Member.objects.get(user=user, semester=review_milestone.assignment.semester)
            if active_sub.count() or not Member.STUDENT in membership.role:
                #logging.debug("I can have assignments")
                # user is a student with an existing submission, or isn't a student
                # allow user to request more tasks manually
                allow_requesting_more_tasks = True
                if not current_tasks.count(): 
                    # automatically assign new tasks to student ONLY if they don't already have tasks
                    #logging.debug("assigning tasks")
                    new_task_count += assign_tasks(review_milestone, user)
        except ObjectDoesNotExist:
            pass

    return dashboard_for(request, user, new_task_count)

@staff_member_required
def student_dashboard(request, username):
    try:
        other_user = User.objects.get(username=username)
    except:
        raise Http404
    return dashboard_for(request, other_user)

def dashboard_for(request, dashboard_user, new_task_count = 0, allow_requesting_more_tasks = False):
    def annotate_tasks_with_counts(tasks):
        return tasks.annotate(comment_count=Count('chunk__comments', distinct=True),
                       reviewer_count=Count('chunk__tasks', distinct=True))
        #logging.log(tasks.all()[0].comment_count)

    all_tasks = dashboard_user.tasks \
        .select_related('submission', 'chunk__file__submission__milestone', 'milestone__assignment__semester__subject')
    active_tasks = all_tasks \
        .exclude(status='C') \
        .exclude(status='U') \
        .order_by('chunk__name', 'submission__name')
    active_tasks = annotate_tasks_with_counts(active_tasks)

    old_completed_tasks = all_tasks \
        .filter(status='C') \
        .exclude(chunk__file__submission__milestone__assignment__semester__is_current_semester=True)
    old_completed_tasks = annotate_tasks_with_counts(old_completed_tasks)

    completed_tasks = all_tasks \
        .filter(status='C') \
        .filter(chunk__file__submission__milestone__assignment__semester__is_current_semester=True) \
        .order_by('completed').reverse()
    completed_tasks = annotate_tasks_with_counts(completed_tasks)

    def collect_submission_data(submissions):
        data = []
        for submission in submissions:
            user_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='U').count()
            static_comments = Comment.objects.filter(chunk__file__submission=submission).filter(type='S').count()
            reviewer_count = User.objects.filter(tasks__chunk__file__submission = submission).count()
            data.append((submission, reviewer_count, submission.last_modified,
                                      user_comments, static_comments))
        return data

    #get all the submissions that the user submitted
    submissions = Submission.objects.filter(authors=dashboard_user) \
        .filter(milestone__duedate__lt=datetime.datetime.now()) \
        .order_by('milestone__duedate')\
        .filter(milestone__assignment__semester__is_current_semester=True)\
        .select_related('chunk__file__assignment') \
        .annotate(last_modified=Max('files__chunks__comments__modified'))\
        .reverse()

    submission_data = collect_submission_data(submissions)

    #get all the submissions that the user submitted, in previous semesters
    old_submissions = Submission.objects.filter(authors=dashboard_user) \
        .filter(milestone__duedate__lt=datetime.datetime.now()) \
        .order_by('milestone__duedate')\
        .exclude(milestone__assignment__semester__is_current_semester=True)\
        .select_related('chunk__file__assignment') \
        .annotate(last_modified=Max('files__chunks__comments__modified'))\
        .reverse()

    old_submission_data = collect_submission_data(old_submissions)

    #find the current submissions
    current_milestones = SubmitMilestone.objects.filter(assignment__semester__members__user=dashboard_user, assignment__semester__members__role=Member.STUDENT, assignment__semester__is_current_semester=True)\
        .filter(assigned_date__lt= datetime.datetime.now())\
        .order_by('duedate')

    current_milestone_data = []
    for milestone in current_milestones:
        try:
            user_extension = milestone.extensions.get(user=dashboard_user)
            extension_days = user_extension.slack_used
        except ObjectDoesNotExist:
            user_extension = None
            extension_days = 0
        if datetime.datetime.now() <= milestone.duedate + datetime.timedelta(days=extension_days) + datetime.timedelta(hours=2):
            current_milestone_data.append((milestone, user_extension))

    #find total slack days left for each membership
    current_memberships = Member.objects.filter(user=dashboard_user, role=Member.STUDENT, semester__is_current_semester=True).select_related('semester__subject')

    current_slack_data = []
    for membership in current_memberships:
        total_slack = membership.slack_budget
        if total_slack > 0:
            used_slack = sum([extension.slack_used for extension in Extension.objects.filter(user=dashboard_user, milestone__assignment__semester=membership.semester)])
            slack_left = total_slack - used_slack
            current_slack_data.append((membership.semester, slack_left))

    return render(request, 'review/dashboard.html', {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'old_completed_tasks': old_completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
        'old_submission_data': old_submission_data,
        'current_milestone_data': current_milestone_data,
        'allow_requesting_more_tasks': allow_requesting_more_tasks,
        'current_slack_data': current_slack_data,
    })

def longest_common_substring(s1, s2):
    m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1 + len(s1)):
        for y in xrange(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest: x_longest]

# def markLogStart(user, log):
#     logStart = Log(user=user, log='LOGSTART: '+str(log), timestamp=datetime.datetime.now())
#     logStart.save()

def find_similar_comment(similar_comment_id, form_text):
    similar_comment = Comment.objects.get(id=similar_comment_id)
    overlap_length = len(longest_common_substring(form_text, similar_comment.text))
    if overlap_length > 20:
        return similar_comment
    else:
        return None

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
        # markLogStart(request.user, {
        #     'type': 'new comment',
        #     'start': start,
        #     'end': end,
        #     'chunk': chunk_id
        # })

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
            try:
                form.similar_comment = find_similar_comment(form.cleaned_data['similar_comment'], form.cleaned_data['text'])
            except:
                form.similar_comment = None
            comment = form.save(commit=False)
            comment.author = request.user
            comment.save()
            user = request.user
            chunk = comment.chunk
            try:
                task = Task.objects.get(
                    chunk=chunk, reviewer=user)
                if task.status == 'N' or task.status == 'O':
                    task.mark_as('S')
            except Task.DoesNotExist:
                pass
            return render(request, 'review/comment.html', {
                'comment': comment,
                'chunk': chunk,
                'snippet': chunk.generate_snippet(comment.start, comment.end),
                'full_view': True,
                'file': chunk.file,
            })


@login_required
def reply(request):
    if request.method == 'GET':
        form = ReplyForm(initial={
            'parent': request.GET['parent']
        })
        # markLogStart(request.user,  {
        #     'type': 'new reply',
        #     'parent': request.GET['parent'],
        # })
        return render(request, 'review/reply_form.html', {'form': form})
    else:
        form = ReplyForm(request.POST)
        if form.is_valid():
            try:
                form.similar_comment = find_similar_comment(form.cleaned_data['similar_comment'], form.cleaned_data['text'])
            except:
                form.similar_comment = None
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
                        reviewer=request.user)
                if task.status == 'N' or task.status == 'O':
                    task.mark_as('S')
            except Task.DoesNotExist:
                pass
            return render(request, 'review/comment.html', {
                'comment': comment,
                'chunk': chunk,
                'snippet': chunk.generate_snippet(comment.start, comment.end),
                'full_view': True,
                'file': chunk.file,
            })
@login_required
def edit_comment(request):
    if request.method == 'GET':
        comment_id = request.GET['comment_id']
        comment = Comment.objects.get(pk=comment_id)
        start = comment.start
        end = comment.end
        try:
            similar_comment = comment.similar_comment.id
        except:
            similar_comment = -1
        form = EditCommentForm(initial={
             'text': comment.text,
             'comment_id': comment.id,
             'similar_comment': similar_comment,
        })
        chunk = Chunk.objects.get(pk=comment.chunk.id)
        # markLogStart(request.user,  {
        #     'type': 'edit comment',
        #     'text': comment.text,
        #     'comment_id': comment.id,
        #     'similar_comment': similar_comment,
        # })
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
            try:
                comment.similar_comment = find_similar_comment(form.cleaned_data['similar_comment'], form.cleaned_data['text'])
            except:
                comment.similar_comment = None
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
                reviewer=request.user)
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
def all_activity(request, review_milestone_id, username):
    user = request.user
    try:
        participant = User.objects.get(username__exact=username)
        #get all assignments
        review_milestone = ReviewMilestone.objects.select_related('submit_milestone', 'assignment__semester').get(id__exact=review_milestone_id)
        user_membership = Member.objects.get(user=user, semester=review_milestone.assignment.semester)
        if not user_membership.is_teacher() and not user==participant and not user.is_staff:
            raise Http404
    except Member.DoesNotExist:
        if not user.is_staff:
            raise Http404
    
    #get all relevant chunks
    chunks = Chunk.objects \
        .filter(file__submission__milestone= review_milestone.submit_milestone) \
        .filter(Q(comments__author=participant) | Q(comments__votes__author=participant)) \
        .select_related('comments__votes', 'comments__author_profile')
    chunk_set = set()
    review_milestone_data = []

    # lexer = JavaLexer()
    formatter = HtmlFormatter(cssclass='syntax', nowrap=True)
    for chunk in chunks:
        if chunk in chunk_set:
            continue
        else:
            chunk_set.add(chunk)
        lexer = get_lexer_for_filename(chunk.file.path)
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

        comments = chunk.comments.prefetch_related('votes', 'author__profile', 'author__membership__semester')
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

@login_required
def change_task(request):
    task_id = request.REQUEST['task_id']
    status = request.REQUEST['status']
    task = get_object_or_404(Task, pk=task_id)
    task.mark_as(status)
    try:
        next_task = request.user.tasks.exclude(status='C').exclude(status='U') \
                                              .order_by('created')[0:1].get()
        return redirect('chunks.views.view_chunk', next_task.chunk_id) if next_task.chunk else redirect('chunks.views.view_all_chunks', 'all', next_task.submission_id)
    except Task.DoesNotExist:
        return redirect('review.views.dashboard')

# => tasks
@login_required
def more_work(request):
    if request.method == 'POST':
        user = request.user
        new_task_count = 0
        current_tasks = user.tasks.exclude(status='C').exclude(status='U')
        total = 0
        if not current_tasks.count():
            live_review_milestones = ReviewMilestone.objects.filter(assigned_date__lt=datetime.datetime.now(),\
                duedate__gt=datetime.datetime.now(), assignment__semester__members_user=user).all()

            for milestone in live_review_milestones:
                current_tasks = user.tasks.filter(milestone=milestone)
                active_sub = Submission.objects.filter(name=user.username, milestone=milestone.reviewmilestone.submit_milestone)
                #do not give tasks to students who got extensions or already have tasks for this assignment
                if (not current_tasks.count()) and active_sub.count():
                    open_assignments = True
                    total += assign_tasks(milestone, user, tasks_to_assign=2)

            active_tasks = user.tasks \
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


def login(request):
    if request.method == 'GET':
        redirect_to = request.GET.get('next', '/')
        return render(request, 'review/login.html', {
            'form': AuthenticationForm(),
            'next': redirect_to
        })
    else:
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return HttpResponseRedirect(redirect_to)

        redirect_to = request.POST.get('next', '/')
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(redirect_to)
        return render(request, 'review/login.html', {
            'form': form,
            'next': redirect_to
        })
def invalid_registration(request):
    invalid_invitation = "Sorry, this invitation has expired. "
    return render(request, 'review/invalidreg.html', {
        'invalid_invitation': invalid_invitation,
    })

def registration_request (request):
    if request.method == 'GET':
        return render(request, 'review/registration_request.html')
    else:
        redirect_to = request.POST.get('next', '/')
        #check if the email is a valid alum email
        email = request.POST['email']
        valid_email = check_email(email)
        if valid_email == True:
            # should send out an email with SHA hash as token
            # redirect to some sort of success page
            send_email(email, request)
            return render(request, 'review/registration_request_complete.html')
    return render(request, 'review/invalidreg.html', {
        'next': redirect_to,
        'invalid_invitation': valid_email
    })

def register(request, email, code):
    invalid_invitation = ""
    if not verify_token(email, code):
        invalid_invitation = "Sorry, this invitation link is invalid."
        return render(request, 'review/invalidreg.html', {
            'invalid_invitation': invalid_invitation,
        })
    if request.method == 'GET':
        redirect_to = request.GET.get('next', '/')
        # render a registration form
        form = UserForm(initial={'email': email, 'username':email.replace("@alum.mit.edu", "")})
    else:
        # create a new user
        form = UserForm(request.POST)
        redirect_to = '/'
        if form.is_valid():
            user = form.save()
            username = request.POST['username']
            password = request.POST['password1']
            user = authenticate(username=username, password=password)
            redirect_to = '/'
            if user is not None:
                if user.is_active:
                    user.profile.role = 'A'
                    user.profile.save()
                    auth.login(request, user)
                    return redirect(redirect_to)
            else:
                return redirect('/')
    return render(request, 'review/register.html', {
        'form': form,
        'next': redirect_to,
        'invalid_invitation': invalid_invitation,
        'email': email
    })

@login_required
def edit_membership(request):
    """Allow users to enroll in classes."""
    user = request.user
    enrolled_classes = request.user.membership

    if request.method == "POST":
        # handle ajax post to this url
        semester_id = request.POST['semester_id']
        semester = Semester.objects.get(pk=semester_id)

        if request.POST['enrolled']=='True':
            m = request.user.membership.filter(semester=semester)
            m.delete()
        else:
            m = Member(user=request.user, role=Member.VOLUNTEER, semester=semester)
            m.save()

    return render(request, 'review/edit_membership.html', {
        'semesters': Semester.objects.filter(is_current_semester=True),
        'enrolled_classes': enrolled_classes,
    })

@login_required
def view_profile(request, username):
    try:
        participant = User.objects.get(username__exact=username)
    except:
        raise Http404
    review_milestone_data = []
    #get all review milestones
    review_milestones = ReviewMilestone.objects.all().order_by('-assigned_date')
    for review_milestone in review_milestones:
        #get all comments that the user wrote
        comments = Comment.objects.filter(author=participant) \
                          .filter(chunk__file__submission__milestone=review_milestone.submit_milestone).select_related('chunk')
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
        user_memberships = request.user.membership.filter(role=Member.TEACHER)
    return render(request, 'review/view_profile.html', {
        'review_milestone_data': review_milestone_data,
        'participant': participant,
        'semesters_taught': Semester.objects.filter(members__in=user_memberships)
    })

@login_required
def edit_profile(request, username):
    # can't edit if not current user
    if request.user.username != username:
        return redirect(reverse('review.views.view_profile', args=([username])))
    """Edit user profile."""
    profile = User.objects.get(username=username).profile

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(reverse('review.views.view_profile', args=([username])))
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'review/edit_profile.html', {
        'form': form
    })

@staff_member_required
def bulk_add(request):
  if request.method == 'GET':
    form = UserBulkAddForm()
    return render(request, 'review/bulk_add_form.html', {
      'form': form
    })
  else: # bulk adding time
    form = UserBulkAddForm(request.POST)
    if not form.is_valid():
      return render(request, 'review/bulk_add_form.html', {
        'form': form,
        'message': 'Invalid form. Are you missing a field?'})

    # todo(mglidden): use a regex instead of three replace statements
    users = form.cleaned_data['users'].replace(' ', ',').replace('\t', ',').replace('\r\n', ',').replace('\n', ',').replace(', ', ',').split(',')

    semester = form.cleaned_data['semester']

    existing_users = 0; created_users = 0; existing_memberships = 0; created_memberships = 0;

    for user_str in users:
      if '@' in user_str:
        user_email = user_str
        user_str = user_email[:user_email.index('@')]
      else:
        user_email = user_str + '@mit.edu'

      # In production, we should never have more than one user for a given email. The dev DB has some bad data, so we're using filter instead of get.
      # We filter by username since that's the unique key.
      users = User.objects.filter(username=user_str)
      if users:
        user = users[0]
        existing_users += 1
      else:
        user = User(username=user_str, email=user_email)
        user.save()
        user.profile.role = 'S'
        user.profile.save()
        created_users += 1

      if not user.membership.filter(semester=semester):
        membership = Member(role=Member.STUDENT, user=user, semester=semester)
        membership.save()
        created_memberships += 1
      else:
        existing_memberships += 1

    return render(request, 'review/bulk_add_form.html', {
      'form': form,
      'message': 'Created %s users, %s already existed. Added %s users to %s, %s were already members.' % (created_users, existing_users, created_memberships, semester, existing_memberships),
      })


@staff_member_required
def reputation_adjustment(request):
    if request.method == 'GET':
        form = ReputationForm()
        return render(request, 'review/reputation_form.html', {
            'form': form,
            'empty': True,
            'success': True,
            'err': ""
        })
    else:
        form = ReputationForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            text.replace('\n', ',')
            pattern = re.compile(r'[\s,]+')
            split_text = pattern.split(text)
            success = True
            err = ""
            if len(split_text) % 2 == 1: #uneven number of tokens
                success = False
                err = "Uneven number of tokens."
            else:
                profiles_to_update = []
                for i in range(0, len(split_text),2):
                    value = 0
                    try:
                        value = int(split_text[i+1])
                    except ValueError:
                        success = False
                        err = str(split_text[i+1]) + " is not an integer."
                        break
                    if re.search('@', split_text[i]): #email
                        try:
                            profile = UserProfile.objects.get(user__email = split_text[i])
                            profiles_to_update.append((profile, value))
                        except ObjectDoesNotExist:
                            success = False
                            err = str(split_text[i]) + " is not a valid email."
                            break
                    else: #assume username
                        try:
                            profile = UserProfile.objects.get(user__username = split_text[i])
                            profiles_to_update.append((profile, value))
                        except ObjectDoesNotExist:
                            success = False
                            err = str(split_text[i]) + " is not a valid username."
                            break
                if success:
                    for profile, value in profiles_to_update:
                        profile.reputation += value
                        profile.save()
                        success = True
            return render(request, 'review/reputation_form.html', {
                'form': form,
                'empty': False,
                'success': success,
                'err': err
            })

@login_required
def allusers(request):
    participants = User.objects.all().exclude(username = 'checkstyle').prefetch_related('profile', 'membership__semester__subject')
    subjects = Subject.objects.all()
    roles = [role[1] for role in Member.ROLE_CHOICES]
    return render(request, 'review/allusers.html', {
        'participants': participants,
        'subjects': subjects,
        'roles': roles,
        'enrolled_classes': request.user,
    })

@login_required
def request_extension(request, milestone_id):
    user = request.user

    # what semester is this milestone in?
    current_milestone = Milestone.objects.get(id=milestone_id)
    semester = current_milestone.assignment.semester
    try:
        membership = Member.objects.get(semester=semester, user=user)
    except:
        raise Http404

    # calculate how much slack budget user has left for this semester
    slack_budget = membership.slack_budget
    used_slack = sum([extension.slack_used for extension in Extension.objects.filter(user=user, milestone__assignment__semester=semester)])
    total_extension_days_left = slack_budget - used_slack

    # get the user's current personal due date for this assignment (including any existing extension)
    try:
        user_duedate = current_milestone.extensions.get(user=user).new_duedate()
    except ObjectDoesNotExist:
        user_duedate = current_milestone.duedate

    # User is going to request an extension
    if request.method == 'GET':
        current_milestone = Milestone.objects.get(id=milestone_id)
        # Make sure user got here legally
        if datetime.datetime.now() > user_duedate + datetime.timedelta(minutes=30):
            return redirect('review.views.dashboard')

        current_extension = (user_duedate - current_milestone.duedate).days

        late_days = 0
        if datetime.datetime.now() > current_milestone.duedate + datetime.timedelta(minutes=30):
            late_days = (datetime.datetime.now() - current_milestone.duedate + datetime.timedelta(minutes=30)).days + 1

        possible_extensions = range(late_days, min(total_extension_days_left+current_extension+1, current_milestone.max_extension+1))

        written_dates = []
        for day in range(max([current_extension]+possible_extensions)+1):
            extension = day * datetime.timedelta(days=1)
            written_dates.append(current_milestone.duedate + extension)


        return render(request, 'review/extension_form.html', {
            'possible_extensions': possible_extensions,
            'current_extension': current_extension,
            'written_dates': written_dates,
            'total_extension_days': total_extension_days_left + current_extension
        })
    else: # user just submitted an extension request
        days = request.POST.get('dayselect', None)
        try:
            current_extension = (user_duedate - current_milestone.duedate).days
            total_extension_days = total_extension_days_left + current_extension

            extension_days = int(days) if days != None else current_extension
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

@staff_member_required
def manage(request):
    return render(request, 'review/manage.html', {
    })

@staff_member_required
def all_extensions(request, milestone_id):
    current_milestone = Milestone.objects.get(id=milestone_id)
    students = User.objects.filter(membership__role=Member.STUDENT, membership__semester=current_milestone.assignment.semester).order_by('username')
    students_with_no_slack = students.exclude(extensions__milestone=current_milestone)
    extensions = Extension.objects.filter(milestone=current_milestone).order_by('user__username').select_related('user__username')

    # the index of a list of students in student_slack is the number of slack days requested by the students in the list
    student_slack = ["".join([str(student)+"\\n" for student in students_with_no_slack])]
    for slack_days in range(1,current_milestone.max_extension+1):
        student_slack.append("".join([str(ext.user.username)+"\\n" for ext in extensions.filter(slack_used=slack_days)]))
    
    return render(request, 'review/all_extensions.html', {
        'current_milestone': current_milestone,
        'student_slack': student_slack
    })
