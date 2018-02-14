#!/usr/bin/env python2.7
import sys, os, django, codecs
import unicodecsv as csv

# set up Django
sys.path.insert(0, "/var/django")
sys.path.insert(0, "/var/django/caesar")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "caesar.settings")
django.setup()

from django.db.models import Q
from django.contrib.auth.models import User
from review.models import Submission, Comment

import datetime


import argparse
parser = argparse.ArgumentParser(description="""
Prints a CSV file of all the comments made on a submission.
""")
parser.add_argument('--submission',
                    metavar="ID",
                    type=int,
                    required=True,
                    help="id number of Submission in Caesar. Go to Admin, Submission, and take the last number from the link of the submission you want all the students to review.")


args = parser.parse_args()

try:
  submission = Submission.objects.get(pk=args.submission)
except Submission.DoesNotExist:
  print "can't find submission #", args.submission
  sys.exit(-1)

writer = csv.DictWriter(sys.stdout, ["username", "created", "text"])
writer.writeheader()
lastTextAndUsername = None
for comment in Comment.objects.filter(chunk__file__submission=submission).order_by("author__username","created").select_related("author"):
    textAndUsername = [comment.text, comment.author.username]
    if textAndUsername != lastTextAndUsername:
        writer.writerow({"username": comment.author.username, "created": comment.created, "text": comment.text})
    lastTextAndUsername = textAndUsername
