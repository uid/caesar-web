#!/usr/bin/env python2.7
import sys, os
# Add a custom Python path.
sys.path.insert(0, "/var/django")
sys.path.insert(0, "/var/django/caesar")

from django.core.management import setup_environ
from caesar import settings
setup_environ(settings)

# Set the DJANGO_SETTINGS_MODULE environment variable.
#os.environ['DJANGO_SETTINGS_MODULE'] = "caesar.settings"

from django.db.models import Q
from caesar.chunks.models import *
from caesar.tasks.models import *
from caesar.review.models import *
from caesar.accounts.models import *

from itertools import chain

from django.core import serializers


import argparse
parser = argparse.ArgumentParser(description="""
Dumps a JSON file containing all the data associated with a particular subject-semester:
- the Members of the course (students & staff) -- this does NOT include their User objects
- the Assignments, Milestones, Submissions, Files, Chunks
- the Tasks and Comments

After dumping a semester, you can delete the semester from the database by selecting it in the admin interface
(/admin/chunks/semester/) and choosing the action Delete selected objects.  You may get a "Chunk matching query does not exist."
after this deletion operation.

To restore a semester, use ./manage.py loaddata your-json-file
You may get errors like
    Column 'assignment_id' cannot be null
or
    DoesNotExist
The workaround is to run loaddata repeatedly until it says something like "Installed N object(s) from 1 fixture(s)".
""")
parser.add_argument('--subject',
                    nargs=1,
                    type=str,
                    required=True,
                    help="name of Subject (for example '6.005'")
parser.add_argument('--semester',
                    nargs=1,
                    type=str,
                    required=True,
                    help="name of Semester (for example 'Fall 2013')")


args = parser.parse_args()
#print args

everything = []

def include(model, filter):
  global everything
  queryset = filter(model.objects)
  print >>sys.stderr, model.__name__ + ": " + str(queryset.count())
  everything = chain(everything, queryset)
  return queryset

subject  = include(Subject,  lambda m: m.filter(name=args.subject[0])).get()
semester = include(Semester, lambda m: m.filter(subject=subject, semester=args.semester[0])).get()

include(Member,      lambda m: m.filter(semester=semester))
include(Assignment,  lambda m: m.filter(semester=semester))
include(Milestone,   lambda m: m.filter(assignment__semester=semester))
include(SubmitMilestone, lambda m: m.filter(assignment__semester=semester))
include(ReviewMilestone, lambda m: m.filter(assignment__semester=semester))
include(Batch,       lambda m: m.filter(submissions__milestone__assignment__semester=semester))
include(Submission,  lambda m: m.filter(milestone__assignment__semester=semester))
include(File,        lambda m: m.filter(submission__milestone__assignment__semester=semester))
include(Chunk,       lambda m: m.filter(file__submission__milestone__assignment__semester=semester))
include(StaffMarker, lambda m: m.filter(chunk__file__submission__milestone__assignment__semester=semester))
include(Task,        lambda m: m.filter(milestone__assignment__semester=semester))
include(Comment,     lambda m: m.filter(chunk__file__submission__milestone__assignment__semester=semester))
include(Vote,        lambda m: m.filter(comment__chunk__file__submission__milestone__assignment__semester=semester))

# members = Member.objects.filter(semester=semester)
# print >>sys.stderr, "Members: " + str(members.count())

# assignments = Assignment.objects.filter(semester=semester)
# print >>sys.stderr, "Assignments: " + str(assignments.count())

# milestones = Milestone.objects.filter(assignment__semester=semester)
# print >>sys.stderr, "Milestones: " + str(milestones.count())

# submitmilestones = SubmitMilestone.objects.filter(assignment__semester=semester)
# print >>sys.stderr, "SubmitMilestones: " + str(submitmilestones.count())

# reviewmilestones = ReviewMilestone.objects.filter(assignment__semester=semester)
# print >>sys.stderr, "ReviewMilestones: " + str(reviewmilestones.count())

# batches = Batch.objects.filter(submissions__milestone__assignment__semester=semester)
# print >>sys.stderr, "Batches: " + str(batches.count())

# submissions = Submission.objects.filter(milestone__assignment__semester=semester)
# print >>sys.stderr, "Submissions: " + str(submissions.count())

# files = File.objects.filter(submission__milestone__assignment__semester=semester)
# print >>sys.stderr, "Files: " + str(files.count())

# chunks = Chunk.objects.filter(file__submission__milestone__assignment__semester=semester)
# print >>sys.stderr, "Chunks: " + str(chunks.count())

# staffmarkers = StaffMarker.objects.filter(chunk__file__submission__milestone__assignment__semester=semester)
# print >>sys.stderr, "StaffMarkers: " + str(staffmarkers.count())

# tasks = Task.objects.filter(milestone__assignment__semester=semester)
# print >>sys.stderr, "Tasks: " + str(tasks.count())

# comments = Comment.objects.filter(chunk__file__submission__milestone__assignment__semester=semester)
# print >>sys.stderr, "Comments: " + str(comments.count())

# votes = Vote.objects.filter(comment__chunk__file__submission__milestone__assignment__semester=semester)
# print >>sys.stderr, "Votes: " + str(votes.count())

# dump everything as JSON
print >>sys.stderr, "before serialize"
data = serializers.serialize("json", everything, indent=2)
print >>sys.stderr, "before final print"
print data
