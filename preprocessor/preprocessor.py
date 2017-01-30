#!/usr/bin/env python2.7
import sys, os, argparse, django

# set up Django
sys.path.insert(0, "/var/django")
sys.path.insert(0, "/var/django/caesar")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "caesar.settings")
django.setup()

ROOT='/var/django/caesar/preprocessor'

import time

# Django imports
from review.models import Assignment, Submission, File, Chunk, Batch, SubmitMilestone
from django.db import transaction

# Preprocessor imports
import parse
from crawler import crawl_submissions
from parse import parse_all_files, parse_staff_code
from checkstyle import generate_checkstyle_comments
from get_milestone import get_milestone

parser = argparse.ArgumentParser(description="""
Load student submissions into Caesar.
""")
parser.add_argument('--subject',
                    nargs=1,
                    type=str,
                    help="name of Subject (in caesar.eecs.mit.edu/admin/subject/; for example '6.005'")
parser.add_argument('--semester',
                    nargs=1,
                    type=str,
                    help="name of Semester (in caesar.eecs.mit.edu/admin/semester/; for example 'Fall 2013')")
parser.add_argument('--milestone',
                    metavar="ID",
                    type=int,
                    help="id number of SubmitMilestone in Caesar. If omitted, uses the latest milestone whose deadline has passed.")
parser.add_argument('-n', '--dry-run',
                    action="store_true",
                    help="just do a test run -- don't save anything into the Caesar database")
args = parser.parse_args()
#print args

# Find the submit milestone object
milestone = get_milestone(args)
print "loading code for milestone", milestone.full_name()

stripTrailingSlash = lambda folder: folder[0:-1] if folder is not None and folder[-1]=='/' else folder


settings = {
    'save_data': not args.dry_run,
    'student_submission_dir': stripTrailingSlash(os.path.join(ROOT, milestone.submitted_code_path)),
    'staff_dir': stripTrailingSlash(os.path.join(ROOT, milestone.starting_code_path)),
    'include': milestone.included_file_patterns.split(),
    'exclude': milestone.excluded_file_patterns.split(),
    'restrict': milestone.restrict_access,
    'generate_comments': milestone.run_checkstyle,
    'suppress_regex': [milestone.suppress_checkstyle_regex],
    }
# print settings

starting_time = time.time()

staff_code = parse_staff_code(settings['staff_dir'], settings['include'], settings['exclude']) if settings['staff_dir'] is not None else {}
#print staff_code.keys()

batch = Batch(name=milestone.full_name())
if settings['save_data']:
  batch.save()
  print "Batch ID: %s" % (batch.id)

# Crawling the file system.
student_code = crawl_submissions(settings['student_submission_dir'], settings['include'], settings['exclude'])

code_objects = parse_all_files(student_code, settings['student_submission_dir'], batch, milestone, settings['save_data'], staff_code, settings['restrict'])

if parse.failed_users:
  print "To add the missing users to Caesar, use scripts/addMembers.py to add the following list of users:"
  print ','.join(parse.failed_users)
  print "Then reload their submissions."

print "Found %s submissions." % (len(code_objects))

if settings['generate_comments']:
  print "Generating checkstyle comments..."
  generate_checkstyle_comments(code_objects, settings['save_data'], batch, settings['suppress_regex'])
