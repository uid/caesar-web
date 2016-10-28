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
parser.add_argument('--checkstyle',
                    action="store_true",
                    help="runs Checkstyle on the students' Java code, and preloads its output as comments in Caesar.")
parser.add_argument('--suppress',
                    action="append",
                    default=[],
                    help="regexes of checkstyle comments to suppress")
parser.add_argument('-n', '--dry-run',
                    action="store_true",
                    help="just do a test run -- don't save anything into the Caesar database")
parser.add_argument('--starting',
                    metavar="PATH",
                    default=None,
                    help="folder containing starting code for the assignment.  Should contain one subfolder, under which is the starting code.")
parser.add_argument('--submissions',
                    metavar="PATH",
                    required=True,
                    help="folder containing student code for the assignment. Should contain subfolders named by student usernames: abc/, def/, ghi/, etc.")
parser.add_argument('--restrict',
                    action="store_true",
                    help="Restrict who can view the students' chunks to the student authors and any assigned reviewers")
parser.add_argument('--include',
                    action="append",
                    default=['*.java', '*.c', '*.h', '*.cpp', '*.CC', '*.py'],
                    help="filename patterns to upload to Caesar; e.g. *Foo*.java matches Foo.java and src/TheFool/Bar.java")
parser.add_argument('--exclude',
                    action="append",
                    default=[],
                    help="filename patterns to exclude from upload")
args = parser.parse_args()
#print args

stripTrailingSlash = lambda folder: folder[0:-1] if folder is not None and folder[-1]=='/' else folder

settings = {
    'submit_milestone_id': args.milestone,
    'generate_comments': args.checkstyle,
    'save_data': not args.dry_run,
    'staff_dir': stripTrailingSlash(args.starting),
    'student_submission_dir': stripTrailingSlash(args.submissions)
    }
#print settings

starting_time = time.time()

# TODO(mglidden)
# Placing the entire preprocessor in a transaction might slow down the database during
# load time, but it will automatically roll back the changes if there's an exception.
# with transaction.commit_on_success():

# Finding the submit milestone object
submit_milestone = SubmitMilestone.objects.get(id=settings['submit_milestone_id'])
print "Found existing submit milestone. Adding code to %s." % (submit_milestone.full_name())

staff_code = parse_staff_code(settings['staff_dir'], args.include, args.exclude) if settings['staff_dir'] is not None else {}
#print staff_code.keys()

batch = Batch(name=submit_milestone.full_name())
if settings['save_data']:
  batch.save()
  print "Batch ID: %s" % (batch.id)

# Crawling the file system.
student_code = crawl_submissions(settings['student_submission_dir'], args.include, args.exclude)

code_objects = parse_all_files(student_code, settings['student_submission_dir'], batch, submit_milestone, settings['save_data'], staff_code, args.restrict)

if parse.failed_users:
  print "To add the missing users to Caesar, use scripts/addMembers.py to add the following list of users:"
  print ','.join(parse.failed_users)
  print "Then reload their submissions."

print "Found %s submissions." % (len(code_objects))

if settings['generate_comments']:
  print "Generating checkstyle comments..."
  generate_checkstyle_comments(code_objects, settings['save_data'], batch, args.suppress)
