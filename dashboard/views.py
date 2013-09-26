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
from review.models import Comment
from tasks.models import Task
from tasks.routing import assign_tasks
from accounts.models import UserProfile, Extension, Member

import datetime
import sys
import logging

import itertools

@login_required
def dashboard(request):
    user = request.user
    new_task_count = 0
    open_assignments = False

    live_review_milestones = ReviewMilestone.objects.filter(assigned_date__lt=datetime.datetime.now(),\
         duedate__gt=datetime.datetime.now(), assignment__semester__members__user=user).all()
    logging.debug('but')
    for review_milestone in live_review_milestones:
        logging.debug('wut')
        current_tasks = user.get_profile().tasks.filter(milestone=review_milestone)
        active_sub = Submission.objects.filter(authors=user, milestone=review_milestone.submit_milestone)
        try:
            membership = Member.objects.get(user=user, semester=review_milestone.assignment.semester)
            #do not give tasks to students who got extensions or already have tasks for this assignment
            #(TODO) refactor member.role to not be so arbitrary
            if (not current_tasks.count()) and (active_sub.count() or not 'student' in membership.role):
                logging.debug('mut')
                open_assignments = True
                new_task_count += assign_tasks(review_milestone, user)
        except ObjectDoesNotExist:
            pass

    old_completed_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission__milestone') \
        .filter(status='C') \
        .exclude(chunk__file__submission__milestone__assignment__semester__is_current_semester=True)
    annotate_tasks_with_counts(old_completed_tasks)

    active_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission__milestone') \
        .exclude(status='C') \
        .exclude(status='U')
    annotate_tasks_with_counts(active_tasks)

    # sort the active tasks before they are sent to the view
    active_tasks = itertools.ifilter(lambda x: x is not None, active_tasks)
    active_tasks = sorted(list(active_tasks), key=lambda x: x.sort_key())

    completed_tasks = user.get_profile().tasks \
        .select_related('chunk__file__submission__milestone') \
        .filter(status='C') \
        .filter(chunk__file__submission__milestone__assignment__semester__is_current_semester=True)
    annotate_tasks_with_counts(completed_tasks)

    #get all the submissions that the user submitted
    submissions = Submission.objects.filter(authors=user) \
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
    old_submissions = Submission.objects.filter(authors=user) \
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
        .filter(assigned_date__lt= datetime.datetime.now())\
        .order_by('duedate')

    current_milestone_data = []
    for milestone in current_milestones:
        try:
            user_extension = milestone.extensions.get(user=user)
            extension_days = user_extension.slack_used
        except ObjectDoesNotExist:
            user_extension = None
            extension_days = 0
        if datetime.datetime.now() <= milestone.duedate + datetime.timedelta(days=extension_days) + datetime.timedelta(hours=2):
            current_milestone_data.append((milestone, user_extension))

    return render(request, 'dashboard/dashboard.html', {
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'old_completed_tasks': old_completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
        'old_submission_data': old_submission_data,
        'current_milestone_data': current_milestone_data,
        'open_assignments': open_assignments,
    })

# => dashboard
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
        .exclude(chunk__file__submission__milestone__assignment__semester__is_current_semester=True)
    annotate_tasks_with_counts(old_completed_tasks)

    active_tasks = participant.get_profile().tasks \
       .select_related('chunk__file__submission_assignment') \
       .exclude(status='C') \
       .exclude(status='U')
    annotate_tasks_with_counts(active_tasks)

    completed_tasks = participant.get_profile().tasks \
       .select_related('chunk__file__submission__assignment') \
       .filter(status='C') \
       .filter(chunk__file__submission__milestone__assignment__semester__is_current_semester=True)
    annotate_tasks_with_counts(completed_tasks)

    #get all the submissions that the participant submitted
    submissions = Submission.objects.filter(authors=participant) \
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
    old_submissions = Submission.objects.filter(authors=participant) \
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
            user_extension = milestone.extensions.get(user=participant)
            current_milestone_data.append((milestone, user_extension))
        except ObjectDoesNotExist:
            current_milestone_data.append((milestone, None))

    return render(request, 'dashboard/dashboard.html', {
        'participant': participant,
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'old_completed_tasks': old_completed_tasks,
        'new_task_count': new_task_count,
        'submission_data': submission_data,
        'old_submission_data': old_submission_data,
        'current_milestone_data': current_milestone_data,
    })


def annotate_tasks_with_counts(tasks):
    tasks.annotate(comment_count=Count('chunk__comments', distinct=True),
                   reviewer_count=Count('chunk__tasks', distinct=True))

