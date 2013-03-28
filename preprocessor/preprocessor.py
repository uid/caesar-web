#!/usr/bin/env python2.7

# Forcing python to search the root Caesar directory.
import sys
sys.path.append('/var/django/caesar/')

# Import settings.py (includes DB settings)
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import time

# Django imports
from chunks.models import Assignment, Submission, File, Chunk, Batch
from django.db import transaction

# Preprocessor imports
import parse
from crawler import crawl_submissions
from parse import parse_all_files, parse_staff_code
from checkstyle import generate_checkstyle_comments

# NOTE: I never tested directories with traling slashes. Sorry I don't have time to make it more robust :(
settings = {
    'assignment_id': 9,
    'assignment_name': 'ps2-beta',
    'generate_comments': False,
    'save_data': True,
    'semester_id': 2,
    'staff_dir': 'Private/ps2/starting-load/starting',
    'student_submission_dir': 'Private/ps2/2day-slack-load'
    }

starting_time = time.time()

# TODO(mglidden)
# Placing the entire preprocessor in a transaction might slow down the database during
# load time, but it will automatically roll back the changes if there's an exception.
# with transaction.commit_on_success():

# Finding / creating the assignment object
assignments = Assignment.objects.filter(id=settings['assignment_id'])
if (len(assignments) > 0): # Adding more submissions to an already-created assignment
  assignment = assignments[0]
  print "Found existing assignment. Adding assignments to %s." % (assignment.name)
elif settings['semester_id']:
  assignment = Assignment(id=settings['assignment_id'], name=settings['assignment_name'], semester_id=settings['semester_id'])
  print "Creating a new assignment. Remember to update the settings: caesar.csail.mit.edu/admin/chunks/assignment/%s" % (settings['assignment_id'])
else:
  print "Must supply an assignment_id or a semester_id (otherwise we don't know which semester to add the assignment to)."
  print "Shutting down preprocessor."
  exit()

staff_code = parse_staff_code(settings['staff_dir'])

batch = Batch(assignment=assignment)
if settings['save_data']:
  batch.save()
  assignment.save()
  print "Batch ID: %s" % (batch.id)

# Crawling the file system.
student_code = crawl_submissions(settings['student_submission_dir'])

code_objects = parse_all_files(student_code, settings['student_submission_dir'], batch, assignment, settings['save_data'], staff_code)

if parse.failed_users:
  print "To add the missing users to Caesar, use scripts/loadusers.py to add the folowing list of users:"
  print ','.join(parse.failed_users)

print "Found %s submissions." % (len(code_objects))

if settings['generate_comments']:
  print "Generating checkstyle comments..."
  generate_checkstyle_comments(code_objects, settings['save_data'], batch)
