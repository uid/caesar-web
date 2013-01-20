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
from parse import parse_files
from checkstyle import generate_checkstyle_comments

settings = {
    'assignment_id': 2,
    'assignment_name': 'ps3',
    'generate_comments': True,
    'save_data': True,
    'semester_id': 1,
    'staff_dir': '~/staff',
    'student_submission_dir': '/home/mglidden/ps3-late',
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

batch = Batch(assignment=assignment)
if settings['save_data']:
  batch.save()
  assignment.save()
  print "Batch ID: %s" % (batch.id)

# Crawling the file system.
student_code = crawl_submissions(settings['student_submission_dir'])

code_objects = [parse_files(username, files, batch, assignment, save=settings['save_data']) for (username, files) in student_code.iteritems()]

if parse.failed_users:
  print "To add the missing users to Caesar, go to caesar.csail.mit.edu/accounts/bulk_add/ and add the folowing list of users:"
  print ','.join(parse.failed_users)

print "Found %s submissions. Generating checkstyle comments." % (len(code_objects))

if settings['generate_comments']:
  generate_checkstyle_comments(code_objects, settings['save_data'])
