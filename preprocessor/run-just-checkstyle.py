#!/usr/bin/env python2.7

# Forcing python to search the root Caesar directory.
import sys
sys.path.append('/var/django/caesar/')

# Import settings.py (includes DB settings)
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from checkstyle import generate_comments
from chunks.models import Chunk, Batch
from django.contrib.auth.models import User

import argparse
parser = argparse.ArgumentParser(description="""
Run checkstyle on chunks already loaded in a batch.
""")
parser.add_argument('--batch',
                    metavar="ID",
                    type=int,
                    required=True,
                    help="id number of Batch in Caesar. Go to Admin, Batch, to find the batch id.")
parser.add_argument('-n', '--dry-run',
                    action="store_true",
                    help="just do a test run -- don't save anything into the Caesar database")

args = parser.parse_args()
#print args

batch = Batch.objects.get(id=args.batch)
checkstyle_user = User.objects.get(username='checkstyle')

# find chunks in the batch that checkstyle hasn't commented on yet
uncommented_chunks = Chunk.objects.filter(file__submission__batch=batch).exclude(comments__author=checkstyle_user)
print "found " + str(len(uncommented_chunks)) + " chunks that checkstyle hasn't commented on"

for chunk in uncommented_chunks:
    comments = generate_comments(chunk, checkstyle_user, batch)
    if not args.dry_run:
        [comment.save() for comment in comments]
