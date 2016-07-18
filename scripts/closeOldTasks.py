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
from caesar.reviews.models import ReviewMilestone, Task

import datetime


import argparse
parser = argparse.ArgumentParser(description="""
Changes status of uncompleted review tasks to Unfinished.
""")
parser.add_argument('--milestone',
                    metavar="ID",
                    type=int,
                    required=True,
                    help="id number of ReviewMilestone in Caesar. Go to Admin, Review milestones, and take the last number from the link of the review milestone you created for this deadline.")
parser.add_argument('-n', '--dry-run',
                    action="store_true",
                    help="just do a test run -- don't save anything into the Caesar database")


args = parser.parse_args()
#print args

tasks = Task.objects.filter(milestone__id=args.milestone).exclude(status='C').exclude(status="U")
print "Preparing to close out " + str(len(tasks)) + " uncompleted tasks"

if not args.dry_run:
  tasks.update(status="U")
  print "Changed the tasks to Unfinished."


