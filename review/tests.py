"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from review.models import *
from chunks.models import *
from django.contrib.auth.models import User

class RoutingTests(TestCase):
    # fixtures = ['6005fall2014.json']
    # fixtures = ['test_fixtures.json']
    # review_milestone = ReviewMilestone.objects.all()[0]
    # reviewer = review_milestone.assignment.semester.members[0]
    # chunks_already_assigned = [task.chunk for task in reviewer.tasks.filter(review_milestone=review_milestone)]
    # chunks_assigned = assign_tasks(review_milestone, reviewer)
    # print review_milestone
    # print reviewer
    # print chunks_already_assigned
    # print chunks_assigned     

    # def test_tasks_pass(self):
    #     """
    #     Count number of tasks that exist
    #     """
    #     # self.assertFalse(Task.objects.all().count() == 28)
    #     print 'chunks:'
    #     print Chunk.objects.all()
    #     c = Chunk.objects.get(id=69000)
    #     print 'name: ' + str(c.name)
    #     print 'changing name to hello...'
    #     c.name = 'hello'
    #     print 'saving name...'
    #     c.save()
    #     self.assertTrue(Chunk.objects.get(id=69000).name == 'hello')

    # def test_tasks_fail(self):
    #     """
    #     Count number of tasks that exist
    #     """
    #     self.assertTrue(Task.objects.all().count() == 64)

    # def test_existence(self):
    #     """
    #     Tests that rcm is actually loaded.
    #     """
    #     self.assertTrue(User.objects.filter(username='rcm').exists())

    # def test_assign_tasks_only_chunks_in_submit_milestone_assigned(self):
    #     """
    #     Tests that only chunks in this SubmitMilestone are assigned
    #     """
    #     for chunk in chunks_assigned:
    #         self.assertTrue(chunk.file.submission.submit_milestone == review_milestone.submit_milestone)

    # def test_assign_tasks_no_duplicate_chunks_assigned(self):
    #     """
    #     Tests that no chunks aready assigned to the reviewer are assigned
    #     """
    #     for chunk in chunks_assigned:
    #         for task_chunk in chunks_already_assigned:
    #             self.assertFalse(chunk == task_chunk)

    # def test_assign_tasks_only_chunks_with_enough_lines_assigned(self):
    #     """
    #     Tests that only chunks with enough lines are assigned
    #     """
    #     for chunk in chunks_assigned:
    #         self.assertTrue(chunk.student_lines <= review_milestone.min_student_lines)

    # def test_assign_tasks_no_chunks_on_list_of_chunks_to_exclude_assigned(self):
    #     """
    #     Tests that no chunks on the list of chunks to exclude are assigned
    #     """
    #     for chunk in chunks_assigned:
    #         self.assertFalse(chunk.name in random_routing.list_chunks_to_exclude(review_milestone))

    # def test_assign_tasks_no_chunks_authored_by_reviewer_assigned(self):
    #     """
    #     Tests that no chunks authored by the reviewer are assigned
    #     """
    #     for chunk in chunks_assigned:
    #         self.assertFalse(reviewer in chunk.file.submission.authors)

