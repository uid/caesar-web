#!/usr/bin/env python2.7
import sys, os, argparse, django

# set up Django
sys.path.insert(0, "/var/django")
sys.path.insert(0, "/var/django/caesar")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "caesar.settings")
django.setup()

import time

# Django imports
from review.models import Assignment, Submission, File, Chunk, Batch, SubmitMilestone
from django.db import transaction

# Preprocessor imports
import parse
from crawler import crawl_submissions
from parse import parse_all_files, parse_staff_code
from checkstyle import generate_checkstyle_comments

parser = argparse.ArgumentParser(description="""
Load student submissions into Caesar.
""")
parser.add_argument('--milestone',
                    metavar="ID",
                    type=int,
                    required=True,
                    help="id number of SubmitMilestone in Caesar. Go to Admin, Submit milestones, and take the last number from the link of the submit milestone you created for this set of submissions.")
# parser.add_argument('--checkstyle',
#                     action="store_true",
#                     help="runs Checkstyle on the students' Java code, and preloads its output as comments in Caesar.")
# parser.add_argument('--suppress',
#                     action="append",
#                     default=[],
#                     help="regexes of checkstyle comments to suppress")
parser.add_argument('-n', '--dry-run',
                    action="store_true",
                    help="just do a test run -- don't save anything into the Caesar database")
# parser.add_argument('--starting',
#                     metavar="PATH",
#                     default=None,
#                     help="folder containing starting code for the assignment.  Should contain one subfolder, under which is the starting code.")
# parser.add_argument('--submissions',
#                     metavar="PATH",
#                     help="folder containing student code for the assignment. Should contain subfolders named by student usernames: abc/, def/, ghi/, etc.")
# parser.add_argument('--restrict',
#                     action="store_true",
#                     help="Restrict who can view the students' chunks to the student authors and any assigned reviewers")
# parser.add_argument('--include',
#                     action="append",
#                     default=['*.java', '*.c', '*.h', '*.cpp', '*.CC', '*.py'],
#                     help="filename patterns to upload to Caesar; e.g. *Foo*.java matches Foo.java and src/TheFool/Bar.java")
# parser.add_argument('--exclude',
#                     action="append",
#                     default=[],
#                     help="filename patterns to exclude from upload")
args = parser.parse_args()
#print args

# Find the submit milestone object
submit_milestone = SubmitMilestone.objects.get(id=args.milestone)
print "Found submit milestone %s." % (submit_milestone.full_name())

stripTrailingSlash = lambda folder: folder[0:-1] if folder is not None and folder[-1]=='/' else folder


settings = {
    'save_data': not args.dry_run,
    'student_submission_dir': stripTrailingSlash(submit_milestone.submittedCodePath),
    'staff_dir': stripTrailingSlash(submit_milestone.startingCodePath),
    'include': submit_milestone.includedFilePatterns.split(),
    'exclude': submit_milestone.excludedFilePatterns.split(),
    'restrict': submit_milestone.restrictAccess,
    'generate_comments': submit_milestone.runCheckstyle,
    'suppress_regex': [submit_milestone.suppressCheckstyleRegex],
    }
print settings

starting_time = time.time()

staff_code = parse_staff_code(settings['staff_dir'], settings['include'], settings['exclude']) if settings['staff_dir'] is not None else {}
#print staff_code.keys()

batch = Batch(name=submit_milestone.full_name())
if settings['save_data']:
  batch.save()
  print "Batch ID: %s" % (batch.id)

# Crawling the file system.
student_code = crawl_submissions(settings['student_submission_dir'], settings['include'], settings['exclude'])

code_objects = parse_all_files(student_code, settings['student_submission_dir'], batch, submit_milestone, settings['save_data'], staff_code, settings['restrict'])

if parse.failed_users:
  print "To add the missing users to Caesar, use scripts/addMembers.py to add the following list of users:"
  print ','.join(parse.failed_users)
  print "Then reload their submissions."

print "Found %s submissions." % (len(code_objects))

if settings['generate_comments']:
  print "Generating checkstyle comments..."
  generate_checkstyle_comments(code_objects, settings['save_data'], batch, settings['suppress_regex'])
