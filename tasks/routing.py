from __future__ import division

from collections import namedtuple, defaultdict
import itertools

from django.db.models import Count
from django.contrib import auth

from chunks import models
from models import Task
import random
import sys
import app_settings

__all__ = ['assign_tasks']

# WARNING: These classes shadow the names of the actual model objects
# that they represent. This is deliberate. I am sorry.
class User:
    def __init__(self, id, role, reputation):
        self.id = id
        self.role = role
        self.reputation = reputation
        self.submissions = []
        self.chunks = []
        self.other_reviewers = set()
        self.clusters = defaultdict(lambda : 0) 

    def __unicode__(self):
        return u"User(id=%d, role=%s, reputation=%d)" % \
                (self.id, self.role, self.reputation)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id

class Submission:
    def __init__(self, id, author, chunks):
        self.id = id
        self.author = author
        self.reviewers = set()
        self.chunks = [Chunk(chunk=chunk, submission=self) 
                for chunk in chunks]

    def __str__(self):
        return unicode(self).encode('utf-8')

class Chunk:
    def __init__(self, chunk, submission):
        self.id = chunk['id']
        self.name = chunk['name']
        self.cluster_id = chunk['cluster_id']
        self.submission = submission
        self.reviewers = set()
        self.class_type = chunk['class_type']
        self.staff_portion = chunk['staff_portion']

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

def _convert_role(role):
    return {'T': 'staff', 'S': 'student'}.get(role, 'other')

def load_users():
    # load all existing users 
    user_map = defaultdict(lambda : None) 
    django_users = auth.models.User.objects.select_related('profile').all()
    for u in django_users:
        user_map[u.id] = User(
                id=u.id,
                role=_convert_role(u.profile.role),
                reputation=u.profile.reputation)
    return user_map


def load_chunks(assignment, user_map, django_user):
    chunks = []
    chunk_map = {}
    submissions = {}

    django_submissions = assignment.submissions.exclude(author=django_user).values()
    django_chunks = models.Chunk.objects \
            .filter(file__submission__assignment=assignment) \
            .exclude(file__submission__author=django_user) \
            .values('id', 'name', 'cluster_id', 'file__submission', 'class_type', 'staff_portion')
    django_tasks = Task.objects.filter(
            chunk__file__submission__assignment=assignment) \
            .exclude(chunk__file__submission__author=django_user) \
                    .select_related('reviewer__user') \

    # load all submissions and chunks into lightweight internal objects
    django_submission_chunks = defaultdict(list)
    for chunk in django_chunks:
        django_submission_chunks[chunk['file__submission']].append(chunk)

    for django_submission in django_submissions:
        submission = Submission(
                id=django_submission['id'],
                author=user_map[django_submission['author_id']],
                chunks=django_submission_chunks[django_submission['id']])
        if not submission.chunks:
            # toss out any submissions without chunks
            continue
        submissions[submission.id] = submission
        chunks.extend(submission.chunks)

    
    # load existing reviewing assignments
    for chunk in chunks:
        chunk_map[chunk.id] = chunk

    for django_task in django_tasks:
        chunk = chunk_map[django_task.chunk_id]
        reviewer = user_map[django_task.reviewer.user_id]
        chunk_map[django_task.chunk_id].assign_reviewer(reviewer)

    return chunks


def find_chunks(user, chunks, count):
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
        if role1 == 'student' and role2 == 'staff' or \
                role1 == 'staff' and role2 == 'student':
            role_affinity = 2
        elif role1 == 'staff' and role2 == 'staff':
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
        if user.role == 'staff':
            def chunk_sort_key(chunk):
                review_priority = len(chunk.reviewers)
                if len(chunk.reviewers) < app_settings.REVIEWERS_PER_CHUNK: 
                    review_priority = 0 
                if chunk.staff_portion >= 80:
                    review_priority = 15
                        
                type_priority = 0
                if (chunk.class_type == 'TEST'):
                    type_priority = 2
                elif (chunk.class_type == 'ENUM'):
                    type_priority = 3
                elif (chunk.class_type == 'EXCE'):
                    type_priority = 4
                return (
                    user in chunk.reviewers,
                    user is chunk.submission.author,
                    review_priority,
                    type_priority,
                    -total_affinity(user, chunk.submission.reviewers),
                    -total_affinity(user, chunk.reviewers),
                )
            return chunk_sort_key
        else:
            def chunk_sort_key(chunk):
                review_priority = len(chunk.reviewers)
                if len(chunk.reviewers) < app_settings.REVIEWERS_PER_CHUNK: 
                    review_priority = 0
                if chunk.staff_portion >= 80:
                    review_priority = 15
                        
                type_priority = 0
                if (chunk.class_type == 'TEST'):
                    type_priority = 2
                elif (chunk.class_type == 'ENUM'):
                    type_priority = 3
                elif (chunk.class_type == 'EXCE'):
                    type_priority = 4
                return (
                    user in chunk.reviewers,
                    user is chunk.submission.author,
                    review_priority,
                    type_priority,
                    chunk.staff_portion,
                    cluster_score(user, chunk),
                    -cluster_sizes[chunk.cluster_id],
                    len(chunk.submission.reviewers),
                    -total_affinity(user, chunk.submission.reviewers),
                    -total_affinity(user, chunk.reviewers),
                )
            return chunk_sort_key
        
    key = make_chunk_sort_key(user)

    if not chunks:
        return
    for _ in itertools.repeat(None, count):
        # TODO consider using a priority queue here
        #random.shuffle(chunks)
        chunk_to_assign = min(chunks, key=key)
        if chunk_to_assign.assign_reviewer(user):
            yield chunk_to_assign.id
        else:
            return


def assign_tasks(assignment, django_user):
    """
    Assigns chunks to the user for review, if the user does not have enough.

    Returns the number of chunks assigned.
    """
    django_profile = django_user.get_profile()
    current_task_count = Task.objects.filter(reviewer=django_profile, 
            chunk__file__submission__assignment=assignment).count()
    
    role = _convert_role(django_profile.role)
    assign_count = app_settings.CHUNKS_PER_ROLE[role] - current_task_count
    if assign_count <= 0:
        return 0

    user_map = load_users()
    user = user_map[django_user.id]
    chunks = load_chunks(assignment, user_map, django_user)
    
    assigned = 0
    for chunk_id in find_chunks(user, chunks, assign_count):
        task = Task(reviewer=django_user.get_profile(), chunk_id=chunk_id)
        task.save()
        assigned += 1
        
    
    return assigned

def more_tasks(assignment, django_user, total):
    sys.stderr.write("more tasks\n")
    django_profile = django_user.get_profile()
    
    role = _convert_role(django_profile.role)
    current_task_count = Task.objects.filter(reviewer=django_profile, 
            chunk__file__submission__assignment=assignment).exclude(status='C').exclude(status='U').count()
    
    assign_count = 0
    if not current_task_count:
        assign_count = total

    if not assign_count:
        return assign_count
        
    user_map = load_users()
    user = user_map[django_user.id]
    chunks = load_chunks(assignment, user_map, django_user)
    
    assigned = 0
    for chunk_id in find_chunks(user, chunks, assign_count):
        task = Task(reviewer=django_user.get_profile(), chunk_id=chunk_id)
        task.save()
        assigned += 1


    return assigned
