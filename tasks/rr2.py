# # run this in console:
# vagrant halt
# vagrant up
# vagrant ssh
# cd /var/django/caesar/
# ./manage.py shell
# from rr2 import *
from __future__ import division
from collections import namedtuple, defaultdict
import itertools
from random import shuffle
from django.db.models import Count
from django.contrib import auth
from django.contrib.auth.models import User
from django.db.models.query import prefetch_related_objects
from tasks.models import Task, app_settings
from chunks.models import Chunk, ReviewMilestone, SubmitMilestone, Assignment, Semester, Milestone, Submission, File
from accounts.models import Member
import random
import sys
import logging
import random_routing
# __all__ = ['assign_tasks']

print
review_milestone = ReviewMilestone.objects.filter(id=2)[0]
reviewer = review_milestone.assignment.semester.members.all()[0].user
# reviewer = User.objects.all()[0]
# assign_tasks(review_milestone, reviewer, tasks_to_assign=None, simulate=True)

test_submission = Submission(milestone=review_milestone.submit_milestone, name="test_submission")
test_submission.save()
test_submission.authors.add(reviewer)
test_file = File(submission=test_submission,path="subs/graves/HIPAddressGenerator.java",data="""/*
 * HIP: Human-Intelligible Positioning
 *
 * (C) 2003 Massachusetts Institute of Technology
 * All rights reserved.
 *
 */

package hip;

import java.util.List;

public interface HIPAddressGenerator {

  /**
   * Return a HIP address <code>hip</code> for a GPS address <code>g</code>, 
   * such that CoordinateSystemResolver.getCoordinateSystem(hip) is
   * contained within <code>root</code>
   */
  public HIPAddress getAddressByEnclosing(GPSAddress g, CoordinateSystem root);

  /**
   * Return all CoordinateSystems that intersect a GPS address <code>g</code>
   * with a coordinate and precision.
   */
  public List getEnclosingCoordinateSystems(GPSAddress g);

}
""")
test_file.save()
test_chunk = Chunk(file=test_file,name="test_chunk",start=0,end=674) 	
test_chunk.save()

chunks = Chunk.objects.all()
print "chunks length = " + str(chunks.count())
# print chunks

chunks = chunks.filter(file__submission__milestone=review_milestone.submit_milestone)
print "chunks_in_review_milesone length = " + str(chunks.count())
# print chunks_in_review_milesone

chunks = chunks.exclude(tasks__reviewer=reviewer)
print "chunks_no_duplicate_reviewers length = " + str(chunks.count())
# print chunks_no_duplicate_reviewers

chunks = chunks.exclude(student_lines__lt=review_milestone.min_student_lines)
print "chunks_enough_lines length = " + str(chunks.count())
# print chunks_enough_lines

chunks = chunks.exclude(name__in=random_routing.list_chunks_to_exclude(review_milestone))
print "chunks_not_excluded length = " + str(chunks.count())
# print chunks_not_excluded

chunks = chunks.annotate(num_tasks=Count('tasks')).exclude(num_tasks__gte=random_routing.num_tasks_for_user(review_milestone, reviewer))
print "chunks_need_more_reviewers length = " + str(chunks.count())
# print chunks_need_more_reviewers

chunks = chunks.exclude(pk__in = chunks.filter(file__submission__authors__id = reviewer.id))
print "chunks_not_by_reviewer length = " + str(chunks.count())
# print chunks_not_by_reviewer

chunks = chunks.select_related('id','file__submission__id','file__submission__authors')
print "chunks_more_info length = " + str(chunks.count())

# chunks = chunks.select_related('id','file__submission__id','file__submission__authors')
# print "chunks_more_info length = " + str(chunks.count())
# # print chunks_more_info

# chunks = [c for c in chunks if reviewer not in c.file.submission.authors.filter()]
# print "chunks_not_by_reviewer length = " + str(len(chunks))

chunks_list = list(chunks)
random.shuffle(chunks_list)
# take the first num_tasks_for_user chunks
chunks_to_assign = chunks_list[:random_routing.num_tasks_for_user(review_milestone, reviewer)]
# if len(chunks_to_assign) < num_tasks_for_user, the reviewer will be assigned fewer
# tasks than they should be and they will be assigned more tasks the next time they
# log in if there are more tasks they can be assigned

# create tasks for the first tasks_to_assign chunks and save them
# for c in chunks_to_assign:
# 	task = Task(reviewer_id=reviewer.id, chunk_id=c.id, milestone=review_milestone, submission_id=c.file.submission.id)
# 	print c

# print
# print "chunks chosen to be tasks"
# print random_routing.assign_tasks(review_milestone, reviewer, tasks_to_assign=None, simulate=True)

# print
# print "chunks chosen to be tasks"
# print random_routing.assign_tasks(review_milestone, reviewer, tasks_to_assign=None, simulate=True)

# print
# print "chunks chosen to be tasks"
# print random_routing.assign_tasks(review_milestone, reviewer, tasks_to_assign=None, simulate=True)

chunk_id_task_map = random_routing.simulate_tasks(review_milestone):
for c in chunk_id_task_map.keys():
  print c
  print chunk_id_task_map[c]
  print
