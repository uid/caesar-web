# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models

class Assignment(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    created = models.DateTimeField()
    class Meta:
        db_table = u'assignments'

class Submission(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    assignment = models.ForeignKey(Assignment)
    created = models.DateTimeField()
    class Meta:
        db_table = u'submissions'

class File(models.Model):
    id = models.IntegerField(primary_key=True)
    path = models.CharField(max_length=200)
    data = models.TextField()
    submission = models.ForeignKey(Submission)
    created = models.DateTimeField()
    class Meta:
        db_table = u'files'
        unique_together = (('path', 'submission'))

class Chunk(models.Model):
    id = models.IntegerField(primary_key=True)
    file = models.ForeignKey(File)
    start = models.IntegerField()
    end = models.IntegerField()
    created = models.DateTimeField()
    class Meta:
        db_table = u'chunks'


