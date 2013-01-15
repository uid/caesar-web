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
from crawler import crawl_submissions
from parse import parse_files
from checkstyle import generate_checkstyle_comments

settings = {
    'assignment_id': 2,
    'assignment_name': 'ps3',
    'generate_comments': True,
    'save_data': True,
    'staff_dir': '~/staff',
    'student_submission_dir': '/home/mglidden/ps3-late',
    }

starting_time = time.time()

# Placing the entire preprocessor in a transaction might slow down the database during
# load time, but it will automatically roll back the changes if there's an exception.
#with transaction.commit_on_success():

# Finding / creating the assignment object
assignments = Assignment.objects.filter(id=settings['assignment_id'])
if (len(assignments) > 0): # Adding more submissions to an already-created assignment
  assignment = assignments[0]
  print "Found existing assignment. Adding assignments to %s." % (assignment.name)
else:
  assignment = Assignment(id=settings['assignment_id'], name=settings['assignment_name'])
  print "Creating a new assignment. Remember to update the settings: caesar.csail.mit.edu/admin/chunks/assignment/%s" % (settings['assignment_id'])

batch = Batch(assignment=assignment)
if settings['save_data']:
  batch.save()
  assignment.save()
  print "Batch ID: %s" % (batch.id)

# Crawling the file system.
student_code = crawl_submissions(settings['student_submission_dir'])

code_objects = [parse_files(username, files, batch, assignment, save=settings['save_data']) for (username, files) in student_code.iteritems()]

print "Found %s submissions. Generating checkstyle comments." % (len(code_objects))

if settings['generate_comments']:
  generate_checkstyle_comments(code_objects, settings['save_data'])
