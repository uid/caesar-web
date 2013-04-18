#!/usr/bin/env python2.7

# Forcing python to search the root Caesar directory.
import sys
sys.path.append('/var/django/caesar/')

# Import settings.py (includes DB settings)
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import time

# Django imports
from chunks.models import Assignment, Submission, File, Chunk, Batch, SubmitMilestone
from django.db import transaction

# Preprocessor imports
import parse
from crawler import crawl_submissions
from parse import parse_all_files, parse_staff_code
from checkstyle import generate_checkstyle_comments

# NOTE: I never tested directories with traling slashes. Sorry I don't have time to make it more robust :(
settings = {
    'submit_milestone_id': 16,
    'generate_comments': True,
    'save_data': False,
    'staff_dir': '/tmp/ps1-staff',
    'student_submission_dir': '/tmp/ps1-submissions'
    }

starting_time = time.time()

# TODO(mglidden)
# Placing the entire preprocessor in a transaction might slow down the database during
# load time, but it will automatically roll back the changes if there's an exception.
# with transaction.commit_on_success():

# Finding the submit milestone object
submit_milestone = SubmitMilestone.objects.get(id=settings['submit_milestone_id'])
print "Found existing submit milestone. Adding code to %s." % (submit_milestone.full_name())

staff_code = parse_staff_code(settings['staff_dir'])

batch = Batch(name=submit_milestone.full_name())
if settings['save_data']:
  batch.save()
  print "Batch ID: %s" % (batch.id)

# Crawling the file system.
student_code = crawl_submissions(settings['student_submission_dir'])

code_objects = parse_all_files(student_code, settings['student_submission_dir'], batch, submit_milestone, settings['save_data'], staff_code)

if parse.failed_users:
  print "To add the missing users to Caesar, use scripts/loadusers.py to add the folowing list of users:"
  print ','.join(parse.failed_users)

print "Found %s submissions." % (len(code_objects))

if settings['generate_comments']:
  print "Generating checkstyle comments..."
  generate_checkstyle_comments(code_objects, settings['save_data'], batch)
