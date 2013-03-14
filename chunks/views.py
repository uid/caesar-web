from chunks.models import Chunk, File, Assignment, ReviewMilestone, Submission, StaffMarker
from chunks.forms import SimulateRoutingForm
from review.models import Comment, Vote, Star
from tasks.models import Task
from tasks.routing import simulate_tasks

from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from pygments import highlight
from pygments.lexers import JavaLexer, SchemeLexer
from pygments.formatters import HtmlFormatter

from simplewiki.models import Article

import os
import subprocess
import datetime
import sys
from collections import defaultdict

@login_required
def view_chunk(request, chunk_id):
    user = request.user
    chunk = get_object_or_404(Chunk, pk=chunk_id)
    if user.profile.is_student() and not chunk.file.submission.assignment().is_current_semester() and user != chunk.file.submission.author:
        raise Http404
    user_votes = dict((vote.comment_id, vote.value) \
            for vote in user.votes.filter(comment__chunk=chunk_id))

    staff_lines = StaffMarker.objects.filter(chunk=chunk).order_by('start_line', 'end_line')

    def get_comment_data(comment):
        vote = user_votes.get(comment.id, None)
        snippet = chunk.generate_snippet(comment.start, comment.end)
        return (comment, vote, snippet)

    comment_data = map(get_comment_data, chunk.comments.select_related('author__profile'))

    # TODO(mglidden): remove
    if chunk.id == 1:
      lexer = SchemeLexer()
    else:
      lexer = JavaLexer()
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
        if task.status == 'N':
            task.mark_as('O')
    except Task.DoesNotExist:
        task = None
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
    })

@login_required
def view_all_chunks(request, viewtype, submission_id):
    user = request.user
    files = File.objects.filter(submission=submission_id).select_related('chunks')
    submission = Submission.objects.get(id = submission_id)
    if not files:
        raise Http404
    milestone = files[0].submission.milestone
    milestone_name = milestone.full_name()
    if user.profile.is_student() and not milestone.assignment.is_current_semester() and user != submission.author:
        raise Http404
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

    lexer = JavaLexer()
    formatter = HtmlFormatter(cssclass='syntax', nowrap=True)
    for afile in files:
        staff_lines = StaffMarker.objects.filter(chunk__file=afile).order_by('start_line', 'end_line')

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

# simulalte?
@login_required
def simualte(request, review_milestone_id):
    user = request.user
    review_milestone = ReviewMilestone.objects.get(id=review_milestone_id)
    milestone_chunks = Chunk.objects.filter(file__submission__milestone__id = review_milestone.submission_milestone.id).select_related('file__submission__milestone', 'profile')

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
            'assignment': review_milestone.assignment,
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
        assignment = review_milestone.assignment
        assignment.students = students
        assignment.alums = alums
        assignment.staff = staff

        assignment.student_count = request.POST['student_tasks']
        assignment.alum_count = request.POST['alum_tasks']
        assignment.staff_count = request.POST['staff_tasks']
        assignment.save()

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
            'assignment': assignment,
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
  def cmp_user_data(user_data1, user_data2):
    user1 = user_data1['user']
    user2 = user_data2['user']
    if user1.profile.role == user2.profile.role:
      return cmp(user1.first_name, user2.first_name)
    if user1.profile.is_student():
      return -1
    if user1.profile.is_staff():
      return 1
    if user2.profile.is_student():
      return 1
    return -1

  def task_dict(task):
    return {
        'completed': task.completed,
        'chunk': task.chunk,
        'author': task.author(),
        'reviewer': task.reviewer,
        'reviewers_dicts': None,
        }
  def chunk_dict(chunk):
    return {
        'reviewer-count': chunk.reviewer_count,
        'id': chunk.id,
        'name': chunk.name,
        'reviewers_dicts': None,
        'tasks': chunk.tasks.all(),
        }

  def reviewers_comment_strs(chunk=None, tasks=None):
    comment_count = defaultdict(int)
    if chunk and (not tasks or len(tasks) == 0):
      for comment in chunk.comments.all():
        comment_count[comment.author.profile] += 1

    if chunk and (not tasks or len(tasks) == 0):
      tasks = chunk.tasks.all()

    checkstyle = []; students = []; alum = []; staff = []
    for task in tasks:
      user_task_dict = {
        'username': task.reviewer.user.username,
        'count': comment_count[task.reviewer],
        'completed': task.completed,
        }

      if task.reviewer.is_student():
        students.append(user_task_dict)
      elif task.reviewer.is_staff():
        staff.append(user_task_dict)
      elif task.reviewer.is_checkstyle():
        checkstyle.append(user_task_dict)
      else:
        alum.append(user_task_dict)

    return [checkstyle, students, alum, staff]

  review_milestone = ReviewMilestone.objects.get(id=review_milestone_id)
  submissions = Submission.objects.filter(milestone__id=review_milestone.submission_milestone.id)
  data = {}
  chunk_task_map = defaultdict(list)
  chunk_map = {}
  form = None

  for submission in submissions:
    data[submission.author.id] = {'tasks': [], 'user': submission.author, 'chunks': [chunk_dict(chunk) for chunk in submission.chunks()], 'submission': submission}
    for chunk in submission.chunks():
      chunk_map[chunk.id] = chunk

  if request.method == 'POST':
    form = SimulateRoutingForm(request.POST)

  if form: #and form.is_valid():
    #chunk_task_map = simulate_tasks(review_milestone, form.cleaned_data['num_students'], form.cleaned_data['num_staff'], form.cleaned_data['num_alum'])
    chunk_task_map = simulate_tasks(review_milestone, 0, 0, 0)

    for (chunk_id, tasks) in chunk_task_map.iteritems():
      for task in tasks:
        if task.reviewer.user.id not in data:
          data[task.reviewer.user.id] = {'tasks': [task_dict(task)], 'user': task.reviewer.user, 'chunks': [], 'submission': None}
        else:
          data[task.reviewer.user.id]['tasks'].append(task_dict(task))

  else:
    for user_id in data.keys():
      for chunk in data[user_id]['chunks']:
        chunk_task_map[chunk['id']] = chunk['tasks']
        for task in chunk['tasks']:
          user_id = task.reviewer.user.id
          if user_id not in data:
            data[user_id] = {'tasks': [task_dict(task)], 'user': task.reviewer.user, 'chunks': [], 'submission': None}
          else:
            data[user_id]['tasks'].append(task_dict(task))

  chunk_reviewers_map = defaultdict(list)
  for (chunk_id, tasks) in chunk_task_map.iteritems():
    chunk_reviewers_map[chunk_id] = reviewers_comment_strs(chunk=chunk_map.get(chunk_id), tasks=tasks)

  for user_data in data.values():
    for chunk in user_data['chunks']:
      chunk['reviewers_dicts'] = chunk_reviewers_map[chunk['id']]
    for task in user_data['tasks']:
      task['reviewers_dicts'] = chunk_reviewers_map[task['chunk'].id]

  return render(request, 'chunks/list_users.html', {'users_data': sorted(data.values(), cmp=cmp_user_data), 'form': SimulateRoutingForm()})
