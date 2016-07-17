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
from caesar.chunks.models import *
from caesar.review.models import *
from caesar.accounts.models import *

from itertools import chain

import argparse
parser = argparse.ArgumentParser(description="""
Dumps a JSON file containing all the data associated with a particular subject-semester:
- the Members of the course (students & staff) -- this does NOT include their User objects
- the Assignments, Milestones, Submissions, Files, Chunks
- the Tasks and Comments

To restore a semester, use ./manage.py loaddata your-json-file
""")
parser.add_argument('--subject',
                    nargs=1,
                    type=str,
                    required=True,
                    help="name of Subject (for example '6.005'")
parser.add_argument('--semester',
                    nargs=1,
                    type=str,
                    required=True,
                    help="name of Semester (for example 'Fall 2013')")


args = parser.parse_args()
#print args

import gc

# code from https://baxeico.wordpress.com/2014/09/30/optimize-django-memory-usage/
# fetches query set in batches, with garbage collections in between, 
# to avoid Django's default behavior of fetching the entire query client-side first
def queryset_iterator(qs, batchsize = 500, gc_collect = True):
    iterator = qs.values_list('pk', flat=True).order_by('pk').distinct().iterator()
    eof = False
    while not eof:
        primary_key_buffer = []
        try:
            while len(primary_key_buffer) < batchsize:
                primary_key_buffer.append(iterator.next())
        except StopIteration:
            eof = True
        for obj in qs.filter(pk__in=primary_key_buffer).order_by('pk').iterator():
            yield obj
        if gc_collect:
            gc.collect()


everything = []

def include(model, filter):
  global everything
  queryset = filter(model.objects)
  print >>sys.stderr, model.__name__ + ": " + str(queryset.count())
  everything = chain(everything, queryset_iterator(queryset))
  return queryset

subject  = include(Subject,  lambda m: m.filter(name=args.subject[0])).get()
semester = include(Semester, lambda m: m.filter(subject=subject, semester=args.semester[0])).get()

include(Member,      lambda m: m.filter(semester=semester))
include(Assignment,  lambda m: m.filter(semester=semester))
include(Milestone,   lambda m: m.filter(assignment__semester=semester))
include(SubmitMilestone, lambda m: m.filter(assignment__semester=semester))
include(ReviewMilestone, lambda m: m.filter(assignment__semester=semester))
include(Batch,       lambda m: m.filter(submissions__milestone__assignment__semester=semester).distinct())
include(Submission,  lambda m: m.filter(milestone__assignment__semester=semester))
include(File,        lambda m: m.filter(submission__milestone__assignment__semester=semester))
include(Chunk,       lambda m: m.filter(file__submission__milestone__assignment__semester=semester))
include(StaffMarker, lambda m: m.filter(chunk__file__submission__milestone__assignment__semester=semester))
include(Task,        lambda m: m.filter(milestone__assignment__semester=semester))
include(Comment,     lambda m: m.filter(chunk__file__submission__milestone__assignment__semester=semester))
include(Vote,        lambda m: m.filter(comment__chunk__file__submission__milestone__assignment__semester=semester))


# get the built-in JSON serializer
from django.core import serializers
JSONSerializer = serializers.get_serializer("json")

modelInProgress = None

# Customize it so that the assignment field is also spit out in the subclasses ReviewMilestone and SubmitMilestone.
# Even though this is redundant (since the superclass Milestone spit is out), without this customization, the default 
# serializer just emits the local fields for each , and manage.py loaddata generates errors ("Warning: Problem installing fixture 
# '6005-sp13.json': Column 'assignment_id' cannot be null") when trying to load it back into the database.
class CustomSerializer(JSONSerializer):
    def get_dump_object(self, obj):
        dump_object = super(CustomSerializer, self).get_dump_object(obj)
        if dump_object["model"] in ["chunks.reviewmilestone", "chunks.submitmilestone"]:
          dump_object["fields"]["assignment"] = obj.assignment_id

        global modelInProgress
        if modelInProgress != dump_object["model"]:
          modelInProgress = dump_object["model"]
          print >>sys.stderr, "writing " + modelInProgress + "..."

        return dump_object


# dump everything as JSON
theSerializer = CustomSerializer()
theSerializer.serialize(everything, indent=2, stream=sys.stdout)

