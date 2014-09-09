from __future__ import division

from collections import namedtuple, defaultdict
import itertools
from random import shuffle

from django.db.models import Count
from django.contrib import auth
from django.contrib.auth.models import User
from django.db.models.query import prefetch_related_objects

from tasks.models import Task, app_settings
from chunks.models import Chunk, ReviewMilestone
from accounts.models import Member
import random
import sys
# import app_settings
import logging

__all__ = ['assign_tasks']

def assign_tasks(review_milestone, reviewer, tasks_to_assign=None, simulate=False):
	# check if tasks_to_assign == None. If true: set it to num required by milestone - num already assigned
	if tasks_to_assign == None:
		tasks_to_assign = num_tasks_for_user(review_milestone, reviewer)
	# get the chunks for the milestone
	# chunks = Chunk.objects \
	# 	.filter(file__submission__milestone = review_milestone.submit_milestone) \
	# 	# remove chunks already assigned to reviewer
	# 	.exclude(tasks__reviewer = r) \
	# 	# remove chunks that have too few student-generated lines
	# 	.exclude(student_lines__lt = review_milestone.min_student_lines) \
	# 	# remove chunks that aren't selected for review
	# 	.exclude(name__in = list_chunks_to_exclude(review_milestone))\
	# 	# remove chunks that already have enough reviewers
	# 	.annotate(num_tasks = Count('tasks')).exclude(num_tasks__gte=num_tasks_for_user(review_milestone, r)) \
	# 	# .values('id', 'name', 'cluster_id', 'file__submission', 'class_type', 'student_lines')\
	# 	.select_related('id','file__submission__id','file__submission__authors')
	

	# get the chunks for the milestone
	chunks = Chunk.objects.all();
	chunks = chunks.filter(file__submission__milestone=review_milestone.submit_milestone)
	# remove chunks already assigned to reviewer
	chunks = chunks.exclude(tasks__reviewer=reviewer)
	# remove chunks that have too few student-generated lines
	chunks = chunks.exclude(student_lines__lt=review_milestone.min_student_lines)
	# remove chunks that aren't selected for review
	chunks = chunks.exclude(name__in=list_chunks_to_exclude(review_milestone))
	# remove chunks that already have enough reviewers
	chunks = chunks.annotate(num_tasks=Count('tasks')).exclude(num_tasks__gte=num_tasks_for_user(review_milestone, reviewer))
	chunks = chunks.exclude(pk__in = chunks.filter(file__submission__authors__id = reviewer.id))
	chunks = chunks.select_related('id','file__submission__id','file__submission__authors')

	# remove chunks that the reviewer authored
	# chunks_to_choose_from = [c for c in chunks if reviewer not in c.file.submission.authors.filter()]
	# randomly order the chunks
	chunks_list = list(chunks)
	random.shuffle(chunks_list)
	# take the first num_tasks_for_user chunks
	chunks_to_assign = chunks_list[:tasks_to_assign]
	# if len(chunks_to_assign) < num_tasks_for_user, the reviewer will be assigned fewer
	# tasks than they should be and they will be assigned more tasks the next time they
	# log in if there are more tasks they can be assigned

	# create tasks for the first tasks_to_assign chunks and save them
	for c in chunks_to_assign:
		task = Task(reviewer_id=reviewer.id, chunk_id=c.id, milestone=review_milestone, submission_id=c.file.submission.id)
		# Why is this here?
		# c.file.submission.reviewers.add(reviewer)
		print c if simulate else task.save()

# this method ignores any tasks already int eh database for this milestone
def simulate_tasks(review_milestone, num_students, num_staff, num_alum):
	reviewers = User.objects.filter(membership__semester=review_milestone.milestone.assignment.semester)
	reviewers_list = list(reviewers)
	random.shuffle(reviewers_list)
	chunk_id_task_map = {}
	user_id_task_map = {}
	for r in reviewers_list:
		# chunks = Chunk.objects \
		# 		.filter(file__submission__milestone=review_milestone.submit_milestone) \
		# 		# don't need to remove chunks already assigned to reviewer because
		# 		# the reviewer doesn't have any chunks assigned to them yet in the simulation
		# 		# .exclude(tasks__reviewer=r) \
		# 		# remove chunks that have too few student-generated lines
		# 		.exclude(student_lines__lt=review_milestone.min_student_lines) \
		# 		# remove chunks that aren't selected for review
		# 		.exclude(name__in=list_chunks_to_exclude(review_milestone))\
		# 		# remove chunks that already have enough reviewers
		# 		.annotate(num_tasks=len(chunk_id_task_map['id'])).exclude(num_tasks__gte=num_tasks_for_user(review_milestone, r)) \
		# 		# .values('id', 'name', 'cluster_id', 'file__submission', 'class_type', 'student_lines')\
		# 		.select_related('id','file__submission__id','file__submission__authors')
		

		# get the chunks for the milestone
		chunks = Chunk.objects.all();
		chunks = chunks.filter(file__submission__milestone=review_milestone.submit_milestone)
		# don't need to remove chunks already assigned to reviewer because
		# the reviewer doesn't have any chunks assigned to them yet in the simulation
		# chunks = chunks.exclude(tasks__reviewer=r)
		# remove chunks that have too few student-generated lines
		chunks = chunks.exclude(student_lines__lt=review_milestone.min_student_lines)
		# remove chunks that aren't selected for review
		chunks = chunks.exclude(name__in=list_chunks_to_exclude(review_milestone))
		# remove chunks that already have enough reviewers
		chunks = chunks.annotate(num_tasks=Count('tasks')).exclude(num_tasks__gte=num_tasks_for_user(review_milestone, r))
		chunks = chunks.select_related('id','file__submission__id','file__submission__authors')



		# remove chunks that the reviewer authored
		chunks_to_choose_from = [c for c in chunks if r not in c.file.submission.authors.filter()]
		# randomly order the chunks
		random.shuffle(chunks_to_choose_from)
		# take the first num_tasks_for_user chunks
		chunks_to_assign = chunks_to_choose_from[:num_tasks_for_user(review_milestone, r)]
		# if len(chunks_to_assign) < num_tasks_for_user, the reviewr will be assigned fewer
		# tasks than they should be and they will be assigned more tasks the next time they
		# log in if there are more tasks they can be assigned
		for c in chunks_to_assign:
			task = Task(reviewer_id=r.id, chunk_id=c.id, milestone=review_milestone, submission_id=c.file.submission.id)
			if c.id in chunk_id_task_map.keys:
				chunk_id_task_map[c.id] += [task]
			else:
				chunk_id_task_map[c.id] = [task]
		return chunk_id_task_map

def num_tasks_for_user(review_milestone, user):
	member = Member.objects.get(user=user, semester=review_milestone.assignment.semester)
	if member.role == Member.STUDENT:
	  return review_milestone.student_count
	elif member.role == Member.TEACHER:
	  return review_milestone.staff_count
	elif member.role == Member.VOLUNTEER:
	  return review_milestone.alum_count
	else:
	  return 0

def list_chunks_to_exclude(review_milestone):
	to_exclude = review_milestone.chunks_to_exclude
	if to_exclude == None:
		return []
	return to_exclude.split(",")