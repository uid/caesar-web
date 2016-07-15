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

from caesar.chunks.models import *
from caesar.tasks.models import *
from caesar.review.models import *
from caesar.accounts.models import *

MODEL_TO_CLASS = {
  "accounts.member": Member,
  "chunks.assignment": Assignment,
  "chunks.batch": Batch,
  "chunks.chunk": Chunk,
  "chunks.file": File,
  "chunks.milestone": Milestone,
  "chunks.reviewmilestone": ReviewMilestone,
  "chunks.semester": Semester,
  "chunks.staffmarker": StaffMarker,
  "chunks.subject": None, # i.e. don't delete these!
  "chunks.submission": Submission,
  "chunks.submitmilestone": SubmitMilestone,
  "review.comment": Comment,
  "review.vote": Vote,
  "tasks.task": Task
}

import re
import argparse
parser = argparse.ArgumentParser(description="""
Given one or more JSON files produced by dumpSemester, deletes the semester's corresponding objects from the database.
""")
parser.add_argument('-n', '--dry-run',
                    action="store_true",
                    help="just do a test run -- don't delete anything from the database")
parser.add_argument('jsonFile',
                    nargs='+',
                    type=argparse.FileType('r'),
                    help="JSON file produced by dumpSemester")


args = parser.parse_args()

for jsonFile in args.jsonFile:
  print "processing " + jsonFile.name

  # although we could read in the json with json.load(), it's faster and uses less memory
  # to scan through it line by line
  primaryKeys = []
  models = []
  for line in jsonFile:
    m = re.search('"pk":\s*(\d+)', line)
    if m:
      primaryKeys.append(int(m.group(1)))
    m = re.search('"model":\s*"(.*)"', line)
    if m:
      modelName = m.group(1)
      assert modelName in MODEL_TO_CLASS
      models.append(modelName)
  jsonFile.close()

  assert len(primaryKeys) == len(models)

  print str(len(primaryKeys)) + " objects in file"

  objectsOfModel = defaultdict(list)
  for (primaryKey, modelName) in reversed(zip(primaryKeys, models)):
    objectsOfModel[modelName].append(primaryKey)

  uniqueModels = reduce(lambda uniq, model: uniq + [model] if len(uniq)==0 or uniq[-1] != model else uniq, models, [])

  for modelName in reversed(uniqueModels):
    modelClass = MODEL_TO_CLASS[modelName]
    if modelClass != None:
      primaryKeys = objectsOfModel[modelName]
      print "deleting " + str(len(primaryKeys)) + " objects from " + modelName
      objectsToDelete = modelClass.objects.filter(id__in=primaryKeys)
      print "   found " + str(objectsToDelete.count()) + " matching objects in the database"
      if args.dry_run:
        print "   (dry run, didn't delete)"
      else:
        print "   deleting...",
        objectsToDelete._raw_delete(objectsToDelete.db);
        print "done"
