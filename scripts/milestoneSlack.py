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
from caesar.chunks.models import SubmitMilestone
from caesar.accounts.models import Extension

import datetime


import argparse
parser = argparse.ArgumentParser(description="""
Prints students and the amount of slack they've requested for a given milestone.
""")
parser.add_argument('--milestone',
                    metavar="ID",
                    type=int,
                    required=True,
                    help="id number of SubmitMilestone in Caesar. Go to Admin, Submit milestones, and take the last number from the link of the submit milestone you created for this deadline.")
parser.add_argument('--only',
                    metavar="N",
                    type=int,
                    default=None,
                    help="if present, only prints students who requested this number of slack days (just usernames, not amount of slack)")


args = parser.parse_args()
#print args

submit_milestone = SubmitMilestone.objects.get(id=args.milestone)

students = User.objects.filter(membership__role="student", membership__semester=submit_milestone.assignment.semester)

# by default, assume everybody has 0 slack
slackForStudent = {}
for student in students:
  slackForStudent[student.username] = 0

# now find out who requested how much
extensions = Extension.objects.filter(milestone=submit_milestone).select_related("user")
for extension in extensions:
  slackForStudent[extension.user.username] = extension.slack_used

# print all students in CSV format, sorted by slack
sortedUsernames = slackForStudent.keys()
sortedUsernames.sort(key=lambda username: (slackForStudent[username],username))

for username in sortedUsernames:
  if args.only == None:
    print username + "," + str(slackForStudent[username])
  elif slackForStudent[username] == args.only:
    print username



