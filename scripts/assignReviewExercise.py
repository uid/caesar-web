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
from django.contrib.auth.models import User
from caesar.chunks.models import Submission,File,Chunk,ReviewMilestone
from caesar.reviews.models import Task, Member

import datetime


import argparse
parser = argparse.ArgumentParser(description="""
Assigns students to review all the files in a particular submission.
""")
parser.add_argument('--submission',
                    metavar="ID",
                    type=int,
                    required=True,
                    help="id number of Submission in Caesar. Go to Admin, Submission, and take the last number from the link of the submission you want all the students to review.")
parser.add_argument('-n', '--dry-run',
                    action="store_true",
                    help="just do a test run -- don't save anything into the Caesar database")
parser.add_argument('usernames',
                    nargs='*',
                    help="usernames of students who should be assigned the files to review")
parser.add_argument('--all-students',
                    action="store_true",
                    help="assign these files to all students in the class, in addition to any usernames specified explicitly")
parser.add_argument('--all-staff',
                    action="store_true",
                    help="assign these files to all staff in the class, in addition to any usernames specified explicitly")


args = parser.parse_args()
print args

try:
  submission = Submission.objects.get(pk=args.submission)
except Submission.DoesNotExist:
  print "can't find submission #", args.submission
  sys.exit(-1)
print "using submission ", submission

semester = submission.milestone.assignment.semester
print "for semester ", semester

try:
  reviewMilestone = ReviewMilestone.objects.get(assignment=submission.milestone.assignment)
except ReviewMilestone.DoesNotExist:
  print "can't find review milestone for this submission's submit milestone; you need to create one in the Caesar Admin page"
  sys.exit(-1)
print "for review milestone ", reviewMilestone

# find the files
files = File.objects.filter(submission_id=args.submission)
print "will assign files ", files

# get the students
query = Q(username__in=args.usernames)
if args.all_students:
  query = query | Q(membership__semester=semester, membership__role=Member.STUDENT)
if args.all_staff:
  query = query | Q(membership__semester=semester, membership__role=Member.TEACHER)
students = User.objects.filter(query).distinct()
print "to reviewers ", students

def get_name(file):
  basename= os.path.basename(file.path)
  root,ext = os.path.splitext(basename)
  return root

# make chunk and task for each student/file pair
tasksCreated = 0
for student in students:
  for file in files:
    chunk = Chunk(file=file, name=get_name(file), start=0, end=len(file.data), class_type='none', staff_portion=0, student_lines=len(file.data.split('\n')))
    if not args.dry_run:
      chunk.save()
    task = Task(chunk=chunk, milestone=reviewMilestone, reviewer=student, submission=submission)
    tasksCreated += 1
    if not args.dry_run:
      task.save()

print tasksCreated, " tasks created"
if not args.dry_run:
  print "and saved to database"
