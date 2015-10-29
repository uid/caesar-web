from accounts.models import Member
from chunks.models import Chunk, File, Assignment, ReviewMilestone, SubmitMilestone, Submission, StaffMarker, Semester
# from chunks.forms import SimulateRoutingForm
from review.models import Comment, Vote, Star
from tasks.models import Task
from tasks.old_routing import simulate_tasks

from django.http import Http404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from pygments import highlight
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from simplewiki.models import Article

import os
import subprocess
import datetime
import sys
import json
from collections import defaultdict
from django.conf import settings

import logging
from operator import itemgetter, attrgetter
from django.utils.datastructures import SortedDict

def get_best_lexer(filename):
    # first see if Pygments knows a good lexer for this filename
    try:
        return get_lexer_for_filename(filename)
    except ClassNotFound:
        pass
    # We use .g4 for Antlr files, but Pygments uses .g
    if filename.endswith(".g4"):
        try:
            return get_lexer_by_name("antlr")
        except ClassNotFound:
            pass
    # fall back to Python lexer
    return get_lexer_by_name("python")

def highlight_chunk_lines(staff_lines, chunk, start=None, end=None):
    lexer = get_best_lexer(chunk.file.path)
    formatter = HtmlFormatter(cssclass='syntax', nowrap=True)

    [numbers, lines] = zip(*chunk.lines[start:end])
    # highlight the code this way to correctly identify multi-line constructs
    # TODO implement a custom formatter to do this instead
    highlighted = zip(numbers,
            highlight(chunk.data, lexer, formatter).splitlines()[start:end])
    highlighted_lines = []
    staff_line_index = 0
    for number, line in highlighted:
        if staff_line_index < len(staff_lines) and number >= staff_lines[staff_line_index].start_line and number <= staff_lines[staff_line_index].end_line:
            while staff_line_index < len(staff_lines) and number == staff_lines[staff_line_index].end_line:
                staff_line_index += 1
            highlighted_lines.append((number, line, True))
        else:
            highlighted_lines.append((number, line, False))
    return highlighted_lines

@login_required
def view_chunk(request, chunk_id):
    user = request.user
    chunk = get_object_or_404(Chunk, pk=chunk_id)
    semester = chunk.file.submission.milestone.assignment.semester
    is_reviewer = Task.objects.filter(chunk=chunk, reviewer=user).exists()

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
            raise PermissionDenied
    except Member.MultipleObjectsReturned:
        raise Http404 # you can't be multiple members for a class so this should never get called
    except Member.DoesNotExist:
        if not user.is_staff:
            raise PermissionDenied # you get a 401 page if you aren't a member of the semester
    
    user_votes = dict((vote.comment_id, vote.value) \
            for vote in user.votes.filter(comment__chunk=chunk_id))

    staff_lines = StaffMarker.objects.filter(chunk=chunk).order_by('start_line', 'end_line')

    def get_comment_data(comment):
        vote = user_votes.get(comment.id, None)
        snippet = chunk.generate_snippet(comment.start, comment.end)
        return (comment, vote, snippet)

    comment_data = map(get_comment_data, chunk.comments.prefetch_related('author__profile', 'author__membership__semester'))

    highlighted_lines = highlight_chunk_lines(staff_lines, chunk)

    task_count = Task.objects.filter(reviewer=user) \
            .exclude(status='C').exclude(status='U').count()
    remaining_task_count = task_count
    # get the associated task if it exists
    try:
        task = Task.objects.get(chunk=chunk, reviewer=user)
        last_task = task_count==1 and not (task.status == 'U' or task.status == 'C')
        if task.status == 'N':
            task.mark_as('O')
        if not (task.status=='U' or task.status=='C'):
            remaining_task_count -= 1
    except Task.DoesNotExist:
        task = None
        if user.is_staff:
            # this is super hacky and it's only here to allow admins to view chunks like a student
            task = Task.objects.filter(chunk=chunk)[0]
        last_task = False

    context = {
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
        'remaining_task_count': remaining_task_count,
    }

    return render(request, 'chunks/view_chunk.html', context)

@login_required
def load_similar_comments(request, chunk_id, load_all_staff_comments):
    if settings.COMMENT_SEARCH:
        user = request.user
        chunk = get_object_or_404(Chunk, pk=chunk_id)
        semester = chunk.file.submission.milestone.assignment.semester
        subject = semester.subject
        membership = Member.objects.filter(user=request.user).filter(semester=semester)
        try:
            role = membership[0].role
        except:
            return HttpResponse()

        if load_all_staff_comments == "True":
            if role == Member.TEACHER:
                similarComments = Comment.objects.filter(author__membership__semester=semester).filter(author__membership__role=Member.TEACHER).filter(chunk__file__submission__milestone__assignment__semester__subject=subject).distinct().prefetch_related('chunk__file__submission__authors__profile', 'author__profile')
            else:
                similarComments = []
        else:
            similarComments = Comment.objects.filter(author=request.user).filter(chunk__file__submission__milestone__assignment__semester__subject=subject).distinct().prefetch_related('chunk__file__submission__authors__profile', 'author__profile')

        similar_comment_data = []
        for comment in similarComments:
            if comment.author.get_full_name():
                author = comment.author.get_full_name()
            else:
                author = comment.author.username
            similar_comment_data.append({
                'comment': comment.text,
                'comment_id': comment.id,
                'chunk_id': comment.chunk.id,
                'author': author,
                'author_username': comment.author.username,
                'reputation': comment.author.profile.reputation,
            })
        return HttpResponse(json.dumps({'similar_comment_data': similar_comment_data}), content_type="application/json")
    return HttpResponse()

@login_required
def highlight_comment_chunk_line(request, comment_id):
    if settings.COMMENT_SEARCH:
        comment = get_object_or_404(Comment, pk=comment_id)
        chunk = comment.chunk
        staff_lines = StaffMarker.objects.filter(chunk=chunk).order_by('start_line', 'end_line')
        # comment.start is a line number, which is 1-indexed
        # start is an index into a list of lines, which is 0-indexed
        start = comment.start-1
        # comment.end is a line number
        # end is an index into a list of lines, which excludes the last line
        end = comment.end
        highlighted_comment_lines = highlight_chunk_lines(staff_lines, comment.chunk, start, end)

        return HttpResponse(json.dumps({
            'comment_id': comment_id,
            'file_id': chunk.file.id,
            'chunk_lines': highlighted_comment_lines,
            }), content_type="application/json")
    # Should never get here
    return HttpResponse() 

@login_required
def view_all_chunks(request, viewtype, submission_id):
    user = request.user
    submission = Submission.objects.get(id = submission_id)
    semester = Semester.objects.get(assignments__milestones__submitmilestone__submissions=submission)
    authors = User.objects.filter(submissions=submission)
    is_reviewer = Task.objects.filter(submission=submission, reviewer=user).exists()

    try:
        user_membership = Member.objects.get(user=user, semester=semester)
        # you get a 404 page ifchrome
        # # you weren't a teacher during the semester
        # #   and
        # # you aren't django staff
        # #   and
        # # you aren't an author of the submission
        if not user_membership.is_teacher() and not user.is_staff and not (user in authors) and not is_reviewer:
            raise PermissionDenied
    except Member.MultipleObjectsReturned:
        raise Http404 # you can't be multiple members for a class so this should never get called
    except Member.DoesNotExist:
        if not user.is_staff:
            raise PermissionDenied # you get a 401 page if you aren't a member of the semester
        
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
        lexer = get_best_lexer(afile.path)
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

                comments = chunk.comments.prefetch_related('chunk', 'author__profile', 'author__membership__semester')
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
      raise PermissionDenied
    submission = Submission.objects.get(milestone=milestone_id, authors__username=username)
    return view_all_chunks(request, viewtype, submission.id)
  except Submission.DoesNotExist or User.DoesNotExist:
    raise Http404
  except Member.DoesNotExist:
    raise PermissionDenied

@login_required
def simulate(request, review_milestone_id):
  review_milestone = ReviewMilestone.objects.prefetch_related('submit_milestone__assignment__semester__members','submit_milestone__assignment__semester__members__user').select_related('submit_milestone','submit_milestone__assignment','submit_milestone__assignment__semester').get(id=review_milestone_id)
  chunk_id_task_map = simulate_tasks(review_milestone)
  return list_users(request, review_milestone_id, simulate=True, chunk_id_task_map=chunk_id_task_map)

@login_required
def list_users(request, review_milestone_id, simulate=False, chunk_id_task_map={}):
  # review_milestone = ReviewMilestone.objects.prefetch_related('submit_milestone__assignment__semester__members','submit_milestone__assignment__semester__members__user').select_related('submit_milestone','submit_milestone__assignment','submit_milestone__assignment__semester').get(id=review_milestone_id)
  # review_milestone = ReviewMilestone.objects.prefetch_related('submit_milestone__assignment__semester__members','submit_milestone__assignment__semester__members__user')
  # review_milestone = review_milestone.select_related('submit_milestone','submit_milestone__assignment','submit_milestone__assignment__semester')
  # review_milestone = review_milestone.get(id=review_milestone_id)
  # submit_milestone = review_milestone.submit_milestone
  review_milestone = ReviewMilestone.objects.select_related('submit_milestone').get(id=review_milestone_id)
  submit_milestone = review_milestone.submit_milestone
  submissions = Submission.objects.filter(milestone=submit_milestone)
  semester = submit_milestone.assignment.semester
  # dictionary mapping user id's to their Member role in the class
  semester_members = dict(semester.members.values_list('user__id','role'))
  member_roles = dict(Member.ROLE_CHOICES)

  # a dictionary mapping all users related to the class to reviewer information
  data = SortedDict()
  data['student'] = []
  data['volunteer'] = []
  data['teacher'] = []
  data['nonmember'] = []
  # TODO: re-implement the form
  # form = None

  # build a dictionary of chunks and their authors
  chunk_id_author_ids_map = defaultdict(lambda : [])
  # build a dictionary of users and their submitted chunks
  user_submitted_chunks = defaultdict(lambda : [])
  # build a dictionary of users and their assigned chunks
  user_assigned_chunks = defaultdict(lambda : [])
  # build a dictionary of chunks and all their info
  chunk_info = {}
  # get all the chunks that were submitted for this milestone
  milestone_chunks = Chunk.objects.filter(file__submission__milestone__id=submit_milestone.id).prefetch_related('tasks','tasks__reviewer')
  
  # populate the chunk_id_author_ids_map dictionary
  milestone_chunks_authors = milestone_chunks.values('id','file__submission__authors').distinct()
  for chunk in milestone_chunks_authors.iterator():
    chunk_id_author_ids_map[chunk['id']].append(chunk['file__submission__authors'])

  # populate the user_submitted_chunks dictionary
  for chunk in milestone_chunks_authors.iterator():
    # get all the authors for the chunk
    author_ids = chunk_id_author_ids_map[chunk['id']]
    # add the chunk to every author's submitted_chunks
    [user_submitted_chunks[author_id].append({'id':chunk['id']}) for author_id in author_ids]

  # # populate the user_assigned_chunks dictionary
  # for chunk in milestone_chunks.all():
  #   # build a dictionary mapping reviewer member roles to their user objects for every task
  #   reviewers = SortedDict()
  #   reviewers['student'] = []
  #   reviewers['volunteer'] = []
  #   reviewers['teacher'] = []
  #   reviewers['nonmember'] = []
  #   num_reviewers = chunk.tasks.count()
  #   if simulate:
  #       if 'tasks' not in chunk_id_task_map[chunk.id]:
  #           chunk_id_task_map[chunk.id]['tasks'] = reviewers 
  #       reviewers = chunk_id_task_map[chunk.id]['tasks']
  #       flattened_reviewers = [val for sublist in reviewers.values() for val in sublist]
  #       num_reviewers = len(flattened_reviewers)
  #       [user_assigned_chunks[reviewer.id].append({'id':chunk.id}) for reviewer in flattened_reviewers]
  #   else:
  #       for task in chunk.tasks.all():
  #           reviewer_role = member_roles.get(semester_members.get(task.reviewer.id))
  #           reviewers[reviewer_role].append(task.reviewer)
  #           user_assigned_chunks[task.reviewer.id].append({'id':chunk.id}) 
  #   # sort the list of reviewers for each role alphabetically
  #   for role in reviewers.keys():
  #     reviewers[role] = sorted(reviewers[role], key=attrgetter('username'))
  #   # map the chunk id to its chunk, reviewers, and number of reviewers
  #   chunk_info[chunk.id] = {"chunk": chunk, "reviewers": reviewers, "num_reviewers": num_reviewers}

  # populate the user_assigned_chunks dictionary
  milestone_chunks_tasks = None
  if simulate:
    milestone_chunks_tasks = milestone_chunks.values('id', 'name').distinct()
  else:
    milestone_chunks_tasks = milestone_chunks.values('id', 'name', 'tasks__id', 'tasks__reviewer__id', 'tasks__reviewer__username').distinct()

  for chunk in milestone_chunks_tasks.iterator():
    # build a dictionary mapping reviewer member roles to their user objects for every task
    reviewers = SortedDict()
    reviewers['student'] = []
    reviewers['volunteer'] = []
    reviewers['teacher'] = []
    reviewers['nonmember'] = []
    # map the chunk id to its chunk, reviewers, and number of reviewers
    if chunk['id'] not in chunk_info:
        chunk_info[chunk['id']] = {"id": chunk['id'], "name": chunk['name'], "reviewers": reviewers, "num_reviewers": 0}

    if simulate:
        if chunk['id'] in chunk_id_task_map.keys():
            reviewers = chunk_id_task_map[chunk['id']]['tasks']
        flattened_reviewers = [val for sublist in reviewers.values() for val in sublist]
        chunk_info[chunk['id']]['reviewers'] = reviewers
        chunk_info[chunk['id']]['num_reviewers'] = len(flattened_reviewers)
        [user_assigned_chunks[reviewer['id']].append({'id':chunk['id']}) for reviewer in flattened_reviewers]
    else:
        if chunk['tasks__reviewer__id'] != None:
            reviewer_role = member_roles.get(semester_members.get(chunk['tasks__reviewer__id']))
            chunk_info[chunk['id']]['reviewers'][reviewer_role].append({'username':chunk['tasks__reviewer__username'],'id':chunk['tasks__reviewer__id']})
            chunk_info[chunk['id']]['num_reviewers'] += 1
            user_assigned_chunks[chunk['tasks__reviewer__id']].append({'id':chunk['id']})


    # num_reviewers = chunk.tasks.count()
    # if simulate:
    #     if 'tasks' not in chunk_id_task_map[chunk.id]:
    #         chunk_id_task_map[chunk.id]['tasks'] = reviewers 
    #     reviewers = chunk_id_task_map[chunk.id]['tasks']
    #     flattened_reviewers = [val for sublist in reviewers.values() for val in sublist]
    #     num_reviewers = len(flattened_reviewers)
    #     [user_assigned_chunks[reviewer.id].append({'id':chunk.id}) for reviewer in flattened_reviewers]
    # else:
    #     for task in chunk.tasks.all():
    
    # # sort the list of reviewers for each role alphabetically
    # for role in reviewers.keys():
    #   reviewers[role] = sorted(reviewers[role], key=attrgetter('username'))
    
  # returns a list of objects that each contain a chunk, the reviewers for that chunk, and the number of reviewers
  def getChunkInfo(user_chunks):
    chunks_list = []
    for chunk in user_chunks:
      chunks_list.append(chunk_info[chunk['id']])
    return sorted(chunks_list, key=itemgetter('num_reviewers'), reverse=True)
    
  # create entries in the data dictionary for every user in the class, user who has a submission in the ReivewMilestone, or user who has a task in the ReviewMilestone
  users = User.objects.filter(Q(membership__semester__id=semester.id) | Q(submissions__milestone__id=submit_milestone.id) | Q(tasks__chunk__file__submission__milestone__id=submit_milestone.id))
  # prefetch related objects we'll need later
  # users = users.select_related('profile').prefetch_related('submissions','submissions__milestone','membership').distinct()
  users = users.order_by('username').values('id','username','first_name','last_name').distinct()
  for user in users:
    # get the User's Submission for this SubmitMilestone
    # TODO: should there only be one Submission allowed per User?
    # user_submission_ids = [submission.id for submission in user.submissions.all() if submission.milestone.id == submit_milestone.id]         
    submitted_chunks = getChunkInfo(user_submitted_chunks[user['id']])
    assigned_chunks = getChunkInfo(user_assigned_chunks[user['id']])
    member_role = member_roles[semester_members[user['id']]] if user['id'] in semester_members else "nonmember"

    all_user_chunks = SortedDict()
    all_user_chunks['submitted'] = submitted_chunks
    all_user_chunks['assigned'] = assigned_chunks
    data[member_role].append({"user": user, "num_chunks_submitted": len(submitted_chunks), "num_chunks_assigned": len(assigned_chunks) ,'chunks': all_user_chunks})

  # users_data = sorted(data.values(), key=itemgetter('num_chunks_submitted', 'num_chunks_assigned'),reverse=True) 
  return render(request, 'chunks/list_users.html', {'users_data': data})

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
