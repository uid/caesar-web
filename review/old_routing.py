from __future__ import division

from collections import namedtuple, defaultdict
import itertools

from django.db.models import Count
from django.contrib import auth
from django.contrib.auth.models import User
from django.db.models.query import prefetch_related_objects

from review.models import Task, Member, Chunk

import random
import sys
import app_settings
import logging

__all__ = ['assign_tasks']

# WARNING: These classes shadow the names of the actual model objects
# that they represent. This is deliberate. I am sorry.
class Reviewer:
    def __init__(self, id, role, reputation):
        self.id = id
        self.role = role
        self.reputation = reputation
        self.submissions = []
        self.chunks = []
        self.other_reviewers = set()
        self.clusters = defaultdict(lambda : 0)

    def __unicode__(self):
        return u"Reviewer(id=%d, role=%s, reputation=%d)" % \
                (self.id, self.role, self.reputation)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id

class SubmissionForReview:
    def __init__(self, id, authors, chunks):
        self.id = id
        self.authors = authors
        self.reviewers = set()
        self.chunks = [ChunkForReview(chunk=chunk, submission=self)
                for chunk in chunks]

    def __str__(self):
        return unicode(self).encode('utf-8')

class ChunkForReview:
    def __init__(self, chunk, submission):
        self.id = chunk.id
        self.name = chunk.name
        self.cluster_id = chunk.cluster_id
        self.submission = submission
        self.reviewers = set()
        self.class_type = chunk.class_type
        self.student_lines = chunk.student_lines
        self.return_count = 0
        self.for_nesting_depth = 0
        self.if_nesting_depth = 0

    def assign_reviewer(self, user):
        if user in self.reviewers:
            return False

        self.reviewers.add(user)
        self.submission.reviewers.add(user)

        user.chunks.append(self)
        user.other_reviewers.update(self.reviewers)
        if self.cluster_id:
            user.clusters[self.cluster_id] += 1

        for reviewer in self.reviewers:
            reviewer.other_reviewers.add(user)
        return True

def _convert_review_milestone_to_priority(review_milestone):
    to_assign = review_milestone.chunk_priorities
    priority_dict = dict()
    for chunk_info in to_assign.split(",")[0:-1]:
        [chunkname, priority] = chunk_info.split(" ")
        priority_dict[chunkname] = -int(priority)
    return priority_dict

def load_members(semester):
    # load all existing users
    user_map = defaultdict(lambda : None)
    members = Member.objects.filter(semester=semester).select_related('user__profile')
    for m in members:
        user_map[m.user_id] = Reviewer(
                id=m.user_id,
                role=m.role,
                reputation=m.user.profile.reputation)
    return user_map


def load_chunks(submit_milestone, user_map, django_user):
    chunks = []
    chunk_map = {}
    submissions = {}

    django_submissions = submit_milestone.submissions.exclude(authors=django_user).prefetch_related("authors")

    # the exclude() in the call below failed because of a Django bug.  Try submit_milestone=55, django_user=1016 on the production db.    
    # django_chunks = Chunk.objects \
    #         .filter(file__submission__milestone=submit_milestone) \
    #         .exclude(file__submission__authors=django_user) \
    #         .prefetch_related('file__submission__authors') \
    #         .values('id', 'name', 'cluster_id', 'file__submission', 'class_type', 'student_lines')

    # using a correct raw SQL query instead..
    django_chunks = Chunk.objects \
        .raw("""
SELECT files.submission_id, `chunks`.`id`, `chunks`.`file_id`, `chunks`.`name`, `chunks`.`start`, `chunks`.`end`, `chunks`.`cluster_id`, `chunks`.`created`, `chunks`.`modified`, `chunks`.`class_type`, `chunks`.`staff_portion`, `chunks`.`student_lines`, `chunks`.`chunk_info`
FROM `chunks` 
join files on chunks.file_id=files.id
join submissions on files.submission_id=submissions.id
join submissions_authors on submissions.id=submissions_authors.submission_id
where submissions.milestone_id=%s and not(user_id=%s)
            """, [submit_milestone.id, django_user.id])
    # preload the file.submission according to http://python.6.x6.nabble.com/Prefetch-related-data-when-using-raw-td4983196.html
    django_chunks = list(django_chunks)
    prefetch_related_objects(django_chunks, ['file__submission'])

    django_tasks = Task.objects.filter(
            submission__milestone=submit_milestone) \
            .exclude(submission__authors=django_user) \
                    .select_related('reviewer', 'chunk') \

    # load all submissions and chunks into lightweight internal objects
    django_submission_chunks = defaultdict(list)
    for chunk in django_chunks:
        django_submission_chunks[chunk.file.submission_id].append(chunk)

    for django_submission in django_submissions:
        submission = SubmissionForReview(
                id=django_submission.id,
                authors=[user_map[author.id] for author in django_submission.authors.all() if author.id in user_map],
                chunks=django_submission_chunks[django_submission.id])
        #logging.debug(django_submission.authors.all())
        #logging.debug(submission.authors)
        if not submission.chunks:
            # toss out any submissions without chunks
            continue
        submissions[submission.id] = submission
        chunks.extend(submission.chunks)
    logging.debug(submissions)

    # load existing reviewing assignments
    for chunk in chunks:
        chunk_map[chunk.id] = chunk
    #logging.debug(chunk_map)

    for django_task in django_tasks:
        if django_task.chunk:
            chunk = chunk_map[django_task.chunk_id] # looks like dead code
            reviewer = user_map[django_task.reviewer_id]
            chunk_map[django_task.chunk_id].assign_reviewer(reviewer)

    return chunks


def find_chunks(user, chunks, count, reviewers_per_chunk, min_student_lines, priority_dict):
    """
    Computes the IDs of the chunks for this user to review on this assignment.

    Does not assign them, this method simply retrieves chunk instances and
    returns a generator of them.
    """

    cluster_sizes = defaultdict(lambda : 0)
    for chunk in chunks:
        if chunk.cluster_id:
            cluster_sizes[chunk.cluster_id] += 1

    # Sort the chunks according to these criteria:
    #
    # For students and other:
    #  1. Remove chunks already assigned to the user
    #  2. Remove chunks with maximum number of reviewers
    #  3. Find chunks with largest number of reviewers
    #  4. Sort those chunks by number of reviewers assigned to submission,
    #     which tries to distribute reviewers fairly among submissions.
    #  5. Maximize affinity between user and reviewers on the submission,
    #     which increases diversity of reviewers for submitter.
    #  6. Maximize affinity between user and reviewers on the chunk, which
    #     increases diversity of other reviewers for reviewer.
    #
    # For staff, we simply try to spread them out to maximize number of
    # submissions with at least one staff member, and then maximize the number
    # of students that get to review a chunk along with staff.

    def compute_affinity(user1, user2):
        distance_affinity = 0
        if user2 in user1.other_reviewers:
            distance_affinity -= 50

        reputation_affinity = abs(user1.reputation - user2.reputation)

        role_affinity = 0
        role1, role2 = user1.role, user2.role
        if role1 == Member.STUDENT and role2 == Member.TEACHER or \
                role1 == Member.TEACHER and role2 == Member.STUDENT:
            role_affinity = 2
        elif role1 == Member.TEACHER and role2 == Member.TEACHER:
            role_affinity = -100
        else:
            role_affinity = (role1 != role2)
        role_affinity *= app_settings.ROLE_AFFINITY_MULTIPLIER

        return distance_affinity + reputation_affinity + role_affinity

    def total_affinity(user, reviewers):
        affinity = 0
        for reviewer in reviewers:
            affinity += compute_affinity(user, reviewer)
        return affinity

    def cluster_score(user, chunk):
        if not chunk.cluster_id:
            return 1
        cluster_count = user.clusters[chunk.cluster_id]
        if cluster_count >= app_settings.CHUNKS_PER_CLUSTER:
            return 2
        else:
            return -cluster_count


    def make_chunk_sort_key(user):
      def chunk_sort_key(chunk):        
        num_nonstaff_reviewers = len([u for u in chunk.reviewers if u.role != Member.TEACHER])
        if user.role == Member.TEACHER:
          # prioritize chunks that are approaching their quota of nonstaff reviewers
          review_priority = max(reviewers_per_chunk - num_nonstaff_reviewers, 0)
          # deprioritize chunks that already have staff reviewers
          review_priority += len([u for u in chunk.reviewers if u.role == Member.TEACHER])
        else:
          if num_nonstaff_reviewers < reviewers_per_chunk:
            review_priority = 0 # high priority!  try to finish the quota on this chunk
          else:
            review_priority = num_nonstaff_reviewers # prioritize chunks with fewer reviewers
        
        if chunk.student_lines <= min_student_lines:
            review_priority = 100000 # deprioritize really short chunks
        
        type_priority = 0
        if chunk.name in priority_dict:
            type_priority = priority_dict[chunk.name]
        elif chunk.class_type == 'TEST' and "StudentDefinedTests" in priority_dict:
            type_priority = priority_dict["StudentDefinedTests"]
        elif chunk.class_type == 'NONE' and "StudentDefinedClasses" in priority_dict:
            type_priority = priority_dict["StudentDefinedClasses"]
        else:
            type_priority = 20
        return (
            user in chunk.reviewers,
            user in chunk.submission.authors,
            review_priority,
            type_priority,
#            -total_affinity(user, chunk.submission.reviewers),
#            -total_affinity(user, chunk.reviewers),
            len(chunk.submission.reviewers),
#                    -1*(chunk.return_count + chunk.for_nesting_depth + chunk.if_nesting_depth),
            -(chunk.student_lines if chunk.student_lines != None else 0),
            random.random()
        )
      return chunk_sort_key
    
    key = make_chunk_sort_key(user)
    
    if not chunks:
        return
    for _ in itertools.repeat(None, count):
        # TODO consider using a priority queue here
        chunk_to_assign = min(chunks, key=key)
        if chunk_to_assign.assign_reviewer(user):
            yield chunk_to_assign.id
        else:
            return

def num_tasks_for_user(review_milestone, user):
    if user.role == Member.STUDENT:
      return review_milestone.student_count
    elif user.role == Member.TEACHER:
      return review_milestone.staff_count
    elif user.role == Member.VOLUNTEER:
      return review_milestone.alum_count
    else:
      return 0

def _generate_tasks(review_milestone, reviewer, chunk_map,  chunk_id_task_map=defaultdict(list), max_tasks=sys.maxint, assign_more=False):
    """
    Returns a list of tasks that should be assigned to the given reviewer.
    assignment: assignment that tasks should be generated for
    reviewer: user object to create more tasks for
    chunk_map: map of chunk ids to chunk object returned by load_chunks. If simulating routing, use the same chunk_map object each time.
    chunk_id_task_map: map of chunk ids to lists of the assigned tasks. If simulating routing, use the same chunk_id_task_map each time.
    """

    #unfinished_task_count = Task.objects.filter(reviewer=reviewer.id, chunk__file__submission__milestone__assignment=assignment).exclude(status='C').count()
    unfinished_tasks = Task.objects.filter(reviewer=reviewer.id, milestone=review_milestone)
    if assign_more:
      unfinished_tasks = unfinished_tasks.exclude(status='C').exclude(status='U')

    unfinished_task_count = unfinished_tasks.count()

    # Should task milestones have num_tasks_for_user?
    num_tasks_to_assign = num_tasks_for_user(review_milestone,reviewer) - unfinished_task_count
    if num_tasks_to_assign <= 0:
      return []

    if unfinished_task_count > 0:
      return []

    num_tasks_to_assign = min(num_tasks_to_assign, max_tasks)

    # Might need to refactor
    chunk_type_priorities = _convert_review_milestone_to_priority(review_milestone)

    tasks = []
    for chunk_id in find_chunks(reviewer, chunk_map.values(), num_tasks_to_assign, review_milestone.reviewers_per_chunk, review_milestone.min_student_lines, chunk_type_priorities):
        submission = chunk_map[chunk_id].submission
        task = Task(reviewer_id=reviewer.id, chunk_id=chunk_id, milestone=review_milestone, submission_id=submission.id)

        chunk_id_task_map[chunk_id].append(task)
        chunk_map[chunk_id].reviewers.add(reviewer)
        submission.reviewers.add(reviewer)
        tasks.append(task)

    return tasks

def assign_tasks(review_milestone, reviewer, tasks_to_assign=sys.maxint, assign_more=False):
  user_map = load_members(review_milestone.assignment.semester)
  chunks = load_chunks(review_milestone.submit_milestone, user_map, reviewer)
  chunk_map = {}
  for chunk in chunks:
    chunk_map[chunk.id] = chunk

  tasks = _generate_tasks(review_milestone, user_map[reviewer.id], chunk_map, max_tasks=tasks_to_assign, assign_more=assign_more)

  [task.save() for task in tasks]

  return len(tasks)

def simulate_tasks(review_milestone, num_students, num_staff, num_alum):
  user_map = load_members(review_milestone.assignment.semester)
  chunks = load_chunks(review_milestone.submit_milestone, user_map, None)
  chunk_map = {}
  for chunk in chunks:
    chunk_map[chunk.id] = chunk
  chunk_id_task_map = defaultdict(list)

  #for i in range(0, num_students + num_staff + num_alum):
  #  if i < num_students:
  #    reviewer =
  #  elif i < num_students + num_staff:
  #    reviewer =
  #  else:
  #    reviewer =
  for reviewer in user_map.values():
    _generate_tasks(review_milestone, user_map[reviewer.id], chunk_map, chunk_id_task_map=chunk_id_task_map)

  return chunk_id_task_map
