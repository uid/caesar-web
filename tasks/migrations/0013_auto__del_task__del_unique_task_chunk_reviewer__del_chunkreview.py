# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # moved these models to review app; don't actually delete them
        # # Removing unique constraint on 'Task', fields ['chunk', 'reviewer']
        # db.delete_unique(u'tasks_task', ['chunk_id', 'reviewer_id'])

        # # Deleting model 'Task'
        # db.delete_table(u'tasks_task')

        # # Deleting model 'ChunkReview'
        # db.delete_table(u'tasks_chunkreview')
        pass


    def backwards(self, orm):
        # Adding model 'Task'
        db.create_table(u'tasks_task', (
            ('status', self.gf('django.db.models.fields.CharField')(default='N', max_length=1)),
            ('started', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('chunk', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', null=True, to=orm['chunks.Chunk'], blank=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', to=orm['chunks.ReviewMilestone'])),
            ('reviewer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', null=True, to=orm['auth.User'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('opened', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', null=True, to=orm['chunks.Submission'], blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('chunk_review', self.gf('django.db.models.fields.related.ForeignKey')(related_name='chunk_review', null=True, to=orm['tasks.ChunkReview'], blank=True)),
            ('completed', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'tasks', ['Task'])

        # Adding unique constraint on 'Task', fields ['chunk', 'reviewer']
        db.create_unique(u'tasks_task', ['chunk_id', 'reviewer_id'])

        # Adding model 'ChunkReview'
        db.create_table(u'tasks_chunkreview', (
            ('chunk', self.gf('django.db.models.fields.related.OneToOneField')(related_name='chunk_review', unique=True, null=True, to=orm['chunks.Chunk'], blank=True)),
            ('staff_reviewers', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('student_or_alum_reviewers', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'tasks', ['ChunkReview'])


    models = {
        
    }

    complete_apps = ['tasks']