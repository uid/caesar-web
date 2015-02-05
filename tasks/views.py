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
from tasks.random_routing import assign_tasks
from review.models import Comment, Vote, Star
from review.forms import CommentForm, ReplyForm, EditCommentForm
from accounts.forms import UserProfileForm
from accounts.models import UserProfile, Extension, Member
from simplewiki.models import Article

import datetime
import sys
import logging

@staff_member_required
def review_milestone_info(request, review_milestone_id):
    review_milestone = get_object_or_404(ReviewMilestone.objects.select_related('assignment__semester'), pk=review_milestone_id)
    submit_milestone = review_milestone.submit_milestone
    comments = Comment.objects.filter(chunk__file__submission__milestone__review_milestone=review_milestone)
    semester = review_milestone.assignment.semester

    total_chunks = Chunk.objects.filter(file__submission__milestone__review_milestone=review_milestone).count()
    alums_participating = Member.objects.filter(role=Member.VOLUNTEER, user__comments__chunk__file__submission__milestone__review_milestone=review_milestone).distinct().count()
    total_tasks = Task.objects.filter(milestone=review_milestone).count()
    assigned_chunks = Chunk.objects.filter(tasks__gt=0).filter(file__submission__milestone__review_milestone=review_milestone).distinct().count()
    total_chunks_with_human = Chunk.objects.filter(comments__type='U').filter(file__submission__milestone__review_milestone=review_milestone).distinct().count()
    total_comments = comments.count()
    total_checkstyle = comments.filter(type='S').count()
    total_staff_comments = comments.filter(author__membership__role=Member.TEACHER, author__membership__semester=semester).count()
    total_student_comments = comments.filter(author__membership__role=Member.STUDENT, author__membership__semester=semester).count()
    total_alum_comments = comments.filter(author__membership__role=Member.VOLUNTEER, author__membership__semester=semester).count()
    total_user_comments = comments.filter(type='U').count()
    zero_chunk_users = len(filter(lambda sub: len(sub.chunks()) == 0, submit_milestone.submissions.all()))

    return render(request, 'tasks/review_milestone_info.html', {
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
    return render(request, 'tasks/stats.html', {
        'chunks': chunks,
        'chunks_with_comments': chunks_with_comments,
        'tasks': tasks,
        'completed_tasks': completed_tasks,
        'recent_comments': recent_comments,
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
        return redirect('dashboard.views.dashboard')

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
    return render(request, 'accounts/manage.html', {
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
    return render(request, 'accountss/manage.html', {
    })


