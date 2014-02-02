from accounts.models import Member
from chunks.models import Chunk, File, Assignment, ReviewMilestone, SubmitMilestone, Submission, StaffMarker, Semester
from chunks.forms import SimulateRoutingForm
from review.models import Comment, Vote, Star
from tasks.models import Task
from tasks.routing import simulate_tasks

from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter

from simplewiki.models import Article

import os
import subprocess
import datetime
import sys
from collections import defaultdict

import logging

@login_required
def view_chunk(request, chunk_id):
    user = request.user
    chunk = get_object_or_404(Chunk, pk=chunk_id)
    semester = chunk.file.submission.milestone.assignment.semester
    is_reviewer = chunk in user.profile.assigned_chunks.all()

    # you get a 404 page if
    # # you weren't a teacher during the semester
    # #   and
    # # you didn't write the code
    # #   and
    # # you weren't assigned to review the code
    # #   and
    # # you aren't a django admin
    try:
        user_membership = Member.objects.get(user=user, semester=semester)
        if not user_membership.is_teacher() and not chunk.file.submission.has_author(user) and not is_reviewer and not user.is_staff:
            raise Http401
    except Member.MultipleObjectsReturned:
        raise Http404 # you can't be multiple members for a class so this should never get called
    except Member.DoesNotExist:
        if not user.is_staff:
            raise Http401 # you get a 401 page if you aren't a member of the semester
    
    user_votes = dict((vote.comment_id, vote.value) \
            for vote in user.votes.filter(comment__chunk=chunk_id))

    staff_lines = StaffMarker.objects.filter(chunk=chunk).order_by('start_line', 'end_line')

    def get_comment_data(comment):
        vote = user_votes.get(comment.id, None)
        snippet = chunk.generate_snippet(comment.start, comment.end)
        return (comment, vote, snippet)

    comment_data = map(get_comment_data, chunk.comments.select_related('author__profile'))

    lexer = get_lexer_for_filename(chunk.file.path)
    
    formatter = HtmlFormatter(cssclass='syntax', nowrap=True)
    numbers, lines = zip(*chunk.lines)
    # highlight the code this way to correctly identify multi-line constructs
    # TODO implement a custom formatter to do this instead
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

    task_count = Task.objects.filter(reviewer=user.get_profile()) \
            .exclude(status='C').exclude(status='U').count()
    # get the associated task if it exists
    try:
        task = Task.objects.get(chunk=chunk, reviewer=user.get_profile())
        last_task = task_count==1 and not (task.status == 'U' or task.status == 'C')
        if task.status == 'N':
            task.mark_as('O')
    except Task.DoesNotExist:
        task = None
        last_task = False

    return render(request, 'chunks/view_chunk.html', {
        'chunk': chunk,
        'similar_chunks': chunk.get_similar_chunks(),
        'highlighted_lines': highlighted_lines,
        'comment_data': comment_data,
        'task': task,
        'task_count': task_count,
        'full_view': True,
        'file': chunk.file,
        'articles': [x for x in Article.objects.all() if not x == Article.get_root()],
        'last_task': last_task,
        'remaining_task_count': task_count if (task.status=='U' or task.status=='C') else task_count-1,
    })

@login_required
def view_all_chunks(request, viewtype, submission_id):
    user = request.user
    submission = Submission.objects.get(id = submission_id)
    semester = Semester.objects.get(assignments__milestones__submitmilestone__submissions=submission)
    authors = User.objects.filter(submissions=submission)

    # block a user who's crawling
    if user.username=="dekehu":
        raise Http404

    try:
        user_membership = Member.objects.get(user=user, semester=semester)
        # you get a 404 page ifchrome
        # # you weren't a teacher during the semester
        # #   and
        # # you aren't django staff
        # #   and
        # # you aren't an author of the submission
        if not user_membership.is_teacher() and not user.is_staff and not (user in authors):
            raise Http401
    except MultipleObjectsReturned:
        raise Http404 # you can't be multiple members for a class so this should never get called
    except DoesNotExist:
        if not user.is_staff:
            raise Http401 # you get a 401 page if you aren't a member of the semester
        
    files = File.objects.filter(submission=submission_id).select_related('chunks')
    if not files:
        raise Http404

    milestone = files[0].submission.milestone
    milestone_name = milestone.full_name()
    
    paths = []
    user_stats = []
    static_stats = []
    all_highlighted_lines = []
    for afile in files:
        paths.append(afile.path)
    common_prefix = ""
    if len(paths) > 1:
        common_prefix = os.path.commonprefix(paths)

    #get a list of only the relative paths
    paths = []
    for afile in files:
        paths.append(os.path.relpath(afile.path, common_prefix))

    formatter = HtmlFormatter(cssclass='syntax', nowrap=True)
    for afile in files:
        staff_lines = StaffMarker.objects.filter(chunk__file=afile).order_by('start_line', 'end_line')
    	lexer = get_lexer_for_filename(afile.path)
        #prepare the file - get the lines that are part of chunk and the ones that aren't
        highlighted_lines_for_file = []
        numbers, lines = zip(*afile.lines)
        highlighted = zip(numbers,
                highlight(afile.data, lexer, formatter).splitlines())

        highlighted_lines = []
        staff_line_index = 0
        for number, line in highlighted:
            if staff_line_index < len(staff_lines) and number >= staff_lines[staff_line_index].start_line and number <= staff_lines[staff_line_index].end_line:
                while staff_line_index < len(staff_lines) and number == staff_lines[staff_line_index].end_line:
                    staff_line_index += 1
                highlighted_lines.append((number, line, True))
            else:
                highlighted_lines.append((number, line, False))

        chunks = afile.chunks.order_by('start')
        total_lines = len(afile.lines)
        offset = numbers[0]
        start = offset
        end = offset
        user_comments = 0
        static_comments = 0
        for chunk in chunks:
            if len(chunk.lines)==0:
                continue
            numbers, lines = zip(*chunk.lines)
            chunk_start = numbers[0]
            chunk_end = chunk_start + len(numbers)
            if end != chunk_start and chunk_start > end: #some lines between chunks
                #non chunk part
                start = end
                end = chunk_start
                #True means it's a chunk, False it's not a chunk
                highlighted_lines_for_file.append((highlighted_lines[start-offset:end - offset], False, None, None))
            if end == chunk_start:
                #get comments and count them
                def get_comment_data(comment):
                    snippet = chunk.generate_snippet(comment.start, comment.end)
                    return (comment, snippet)

                comments = chunk.comments.select_related('chunk', 'author__profile')
                comment_data = map(get_comment_data, comments)

                user_comments += comments.filter(type='U').count()
                static_comments += comments.filter(type='S').count()

                #now for the chunk part
                start = chunk_start
                end = chunk_end
                #True means it's a chunk, False it's not a chunk
                highlighted_lines_for_file.append((highlighted_lines[start-offset:end-offset], True, chunk, comment_data))
        #see if there is anything else to grab
        highlighted_lines_for_file.append((highlighted_lines[end-offset:], False, None, None))
        user_stats.append(user_comments)
        static_stats.append(static_comments)
        all_highlighted_lines.append(highlighted_lines_for_file)
    file_data = zip(paths, all_highlighted_lines, files)

    code_only = False
    comment_view = True
    if viewtype == "code":
        code_only = True
        comment_view = False

    path_and_stats = zip(paths, user_stats, static_stats)

    return render(request, 'chunks/view_all_chunks.html', {
        'milestone_name': milestone_name,
        'path_and_stats': path_and_stats,
        'file_data': file_data,
        'code_only': code_only,
        'read_only': False,
        'comment_view': comment_view,
        'full_view': True,
        'articles': [x for x in Article.objects.all() if not x == Article.get_root()],
    })

@login_required
def view_submission_for_milestone(request, viewtype, milestone_id, username):
  user = request.user
  try:
    semester = SubmitMilestone.objects.get(id=milestone_id).assignment.semester
    member = Member.objects.get(semester=semester, user=user)
    author = User.objects.get(username__exact=username)
    if not member.is_teacher() and not user==author and not user.is_staff:
      raise Http401
    submission = Submission.objects.get(milestone=milestone_id, authors__username=username)
    return view_all_chunks(request, viewtype, submission.id)
  except Submission.DoesNotExist or User.DoesNotExist:
    raise Http404
  except Member.DoesNotExist:
    raise Http401

@login_required
def simulate(request, review_milestone_id):
    user = request.user
    review_milestone = ReviewMilestone.objects.get(id=review_milestone_id)
    milestone_chunks = Chunk.objects.filter(file__submission__milestone=review_milestone.submit_milestone).select_related('file__submission__milestone', 'profile')

    chunks_graph = dict()
    edited = set()
    test = set()
    staff_provided = set()
    max_important = 0
    max_test = 0
    max_unimportant = 0
    for chunk in milestone_chunks:
        name = chunk.name
        if name is None:
            continue
        lines_dict = dict()
        num = 0
        if name in chunks_graph:
            lines_dict, num = chunks_graph[name]
        lines = min(chunk.student_lines, 200)
        if lines in lines_dict:
            copies = lines_dict[lines]
            if not (lines == 200 and copies == 10):
                lines_dict[lines] += 1
        else:
            lines_dict[lines] = 1
        if lines > 30 and chunk.class_type == "NONE":
            edited.add(name)
        if num>40:
            staff_provided.add(name)
        if chunk.class_type == "TEST":
            test.add(name)
        chunks_graph[name] = (lines_dict, num+1)

    #list of lists ["sudoku", [[1,20], [3,50]]]
    #list of important and unimportant
    important_graphs = []
    test_graphs = []
    unimportant_graphs = []
    other_test = set()
    other = set()
    for name in chunks_graph.keys():
        lines_dict, num = chunks_graph[name]
        lines_list = []
        max_copy = 0
        for key in lines_dict.keys():
            lines_list.append([int(key), lines_dict[key]])
            max_copy = max(max_copy, lines_dict[key])
        if name in test:
            max_test = max(max_test, max_copy)
            if name in staff_provided:
                test_graphs.append([name, lines_list])
            else:
                other_test.add(name)
        elif name in edited and name in staff_provided:
            max_important = max(max_important, max_copy)
            important_graphs.append([name, lines_list])
        else:
            max_unimportant = max(max_unimportant, max_copy)
            if name in staff_provided:
                unimportant_graphs.append([name, lines_list])
            else:
                other.add(name)

    #call everything student created as "other"
    lines_list = []
    for name in other_test:
        lines_dict, num = chunks_graph[name]
        for key in lines_dict.keys():
            lines_list.append([int(key), lines_dict[key]])
    if len(lines_list) > 0:
        test_graphs.append(["StudentDefinedTests", lines_list])
    lines_list = []
    for name in other:
        lines_dict, num = chunks_graph[name]
        for key in lines_dict.keys():
            lines_list.append([int(key), lines_dict[key]])
    if len(lines_list) > 0:
        unimportant_graphs.append(["StudentDefinedClasses", lines_list])

    chunks_data = []

    for name, lines_list in important_graphs:
        chunks_data.append((name, 1))
    for name, lines_list in unimportant_graphs:
        chunks_data.append((name, 1))
    for name, lines_list in test_graphs:
	    chunks_data.append((name, 0))

    if request.method == 'GET':
        to_assign = review_milestone.chunks_to_assign
        if to_assign is not None:
            count = 0
            for chunk_info in to_assign.split(",")[0:-1]:
                split_info = chunk_info.split(" ")
                chunks_data[count] = (split_info[0], int(split_info[1]))
                count += 1


        return render(request, 'chunks/simulate.html', {
            'review_milestone': review_milestone,
            'chunks_data': chunks_data,
            'important_graph': important_graphs,
            'unimportant_graph': unimportant_graphs,
            'test_graph': test_graphs,
            'max_important': max_important+1,
            'max_unimportant': max_unimportant+1,
            'max_test': max_test +1,
        })
    else:
        students = request.POST['students']
        alums = request.POST['alums']
        staff = request.POST['staff']
        review_milestone.students = students
        review_milestone.alums = alums
        review_milestone.staff = staff

        review_milestone.student_count = request.POST['student_tasks']
        review_milestone.alum_count = request.POST['alum_tasks']
        review_milestone.staff_count = request.POST['staff_tasks']
        review_milestone.reviewers_per_chunk = request.POST['per_chunk']
        review_milestone.min_student_lines = request.POST['min_lines']
        review_milestone.save()

        chunks_raw = request.POST.getlist('chunk')
        checked = set()
        for raw in chunks_raw:
            checked.add(raw)

        to_assign = ""
        for name, check in chunks_data:
            if name in checked:
                to_assign += name + " 1,"
            else:
                to_assign += name + " 0,"


        if len(to_assign) > 1:
            count = 0
            for chunk_info in to_assign.split(",")[0:-1]:
                split_info = chunk_info.split(" ")
                chunks_data[count] = (split_info[0], int(split_info[1]))
                count += 1

        review_milestone.chunks_to_assign = to_assign
        review_milestone.save()


        return render(request, 'chunks/simulate.html', {
            'review_milestone': review_milestone,
            'chunks_data': chunks_data,
            'important_graph': important_graphs,
            'unimportant_graph': unimportant_graphs,
            'test_graph': test_graphs,
            'max_important': max_important+1,
            'max_unimportant': max_unimportant+1,
            'max_test': max_test +1,
        })

@login_required
def list_users(request, review_milestone_id):
  # def cmp_user_data(user_data1, user_data2):
  #   user1 = user_data1['user']
  #   user2 = user_data2['user']
  #   # change this to use their member role in the class
  #   if user1.profile.role == user2.profile.role:
  #     return cmp(user1.first_name, user2.first_name)
  #   if user1.profile.is_student():
  #     return -1
  #   if user1.profile.is_staff():
  #     return 1
  #   if user2.profile.is_student():
  #     return 1
  #   return -1

  def task_dict(task):
    return {
        'completed': task.completed,
        'chunk': task.chunk,
        'author': task.author(),
        'reviewer': task.reviewer,
        'reviewers_dicts': None,
        }
  def chunk_dict(chunk):
    return 

  def reviewers_comment_strs(chunk=None, tasks=None):
    comment_count = defaultdict(int)
    if chunk and (not tasks or len(tasks) == 0):
      for comment in chunk.comments.all():
        comment_count[comment.author.profile] += 1

    #if chunk and (not tasks or len(tasks) == 0):
    #  tasks = chunk.tasks.all()

    checkstyle = []; students = []; alum = []; staff = []
    for task in tasks:
      user_task_dict = {
        'username': task.reviewer.user.username,
        'count': comment_count[task.reviewer],
        'completed': task.completed,
        }

      member = task.reviewer.user.memberships.objects.get(user=task.reviewer.user, semester=task.milestone.assignment.semester)
      if member.is_student():
        students.append(user_task_dict)
      elif member.is_teacher():
        staff.append(user_task_dict)
      elif member.is_volunteer():
        alum.append(user_task_dict)
      elif task.reviewer.is_checkstyle():
        checkstyle.append(user_task_dict)

    return [checkstyle, students, alum, staff]

  review_milestone = ReviewMilestone.objects.get(id=review_milestone_id)
  submissions = Submission.objects.filter(milestone=review_milestone.submit_milestone)
  assignment_id = review_milestone.submit_milestone.id

  data = {}
  chunk_task_map = defaultdict(list)
  chunk_map = {}
  form = None

  for user in User.objects.select_related('profile').filter(Q(submissions__milestone__id=assignment_id) | Q(profile__tasks__chunk__file__submission__milestone__id=assignment_id)):
      data[user.id] = {'tasks': [], 'user': user, 'chunks': [], 'has_chunks': False, 'submission': None}

  for submission in Submission.objects.select_related('author__profile').filter(milestone__id=assignment_id):
      data[submission.author_id]['submission'] = submission

  for chunk in Chunk.objects.select_related('file__submission').filter(file__submission__milestone__id=assignment_id):
      chunk_map[chunk.id] = chunk
      authorid = chunk.file.submission.author_id
      data[authorid]['chunks'].append({
        'reviewer-count': chunk.reviewer_count(),
        'id': chunk.id,
        'name': chunk.name,
        'reviewers_dicts': None,
        'tasks': [],
        })
      data[authorid]['has_chunks'] = True
      
  for task in Task.objects.select_related('chunk__file__submission__author', 'reviewer__user').filter(chunk__file__submission__milestone__id=assignment_id):
      authorid = task.chunk.file.submission.author_id
      chunkid = task.chunk_id
      for chunk in data[authorid]['chunks']:
          if chunk["id"] == chunkid:
              chunk["tasks"].append(task)

  if request.method == 'POST':
    form = SimulateRoutingForm(request.POST)

  if form: #and form.is_valid():
    #chunk_task_map = simulate_tasks(review_milestone, form.cleaned_data['num_students'], form.cleaned_data['num_staff'], form.cleaned_data['num_alum'])
    chunk_task_map = simulate_tasks(review_milestone, 0, 0, 0)

    for (chunk_id, tasks) in chunk_task_map.iteritems():
      for task in tasks:
        if task.reviewer.userid not in data:
          data[task.reviewer.user_id] = {'tasks': [task_dict(task)], 'user': task.reviewer.user, 'chunks': [], 'submission': None}
        else:
          data[task.reviewer.user_id]['tasks'].append(task_dict(task))

  else:

    for user_id in data.keys():
      for chunk in data[user_id]['chunks']:
        chunk_task_map[chunk['id']] = chunk['tasks']
        for task in chunk['tasks']:
          user_id = task.reviewer.user_id
          data[user_id]['tasks'].append(task_dict(task))

  chunk_reviewers_map = defaultdict(list)
  
  for user_data in data.values():
    for chunk in user_data['chunks']:
      chunk['reviewers_dicts'] = chunk_reviewers_map[chunk['id']]
    for task in user_data['tasks']:
      task['reviewers_dicts'] = chunk_reviewers_map[task['chunk'].id]

  return render(request, 'chunks/list_users.html', {'users_data': sorted(data.values(), cmp=cmp_user_data), 'form': SimulateRoutingForm()})

@login_required
def publish_code(request):
    """Allow users to publish their written code."""
    submissions = Submission.objects.filter(authors=request.user)

    if request.method == "POST":
        # handle ajax post to this url
        submission_id = request.POST['submission_id']
        submission = Submission.objects.get(pk=submission_id)
        if not submission.has_author(request.user):
            raise PermissionDenied

        if request.POST['published']=='False':
            logging.info('Publishing!')
            submission.published = True
            submission.save()
        else:
            logging.info('Unpublishing!')
            submission.published = False
            submission.save()

    return render(request, 'chunks/publish_code.html', {
        'user': request.user,
        'submissions': submissions,
    })
