# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # # Deleting model 'UserProfile'
        # db.delete_table(u'accounts_userprofile')

        # # Deleting model 'Member'
        # db.delete_table(u'accounts_member')

        # # Deleting model 'Extension'
        # db.delete_table(u'accounts_extension')

        # skip deleting, because we're just moving these models to the review app
        pass

    def backwards(self, orm):
        # Adding model 'UserProfile'
        db.create_table(u'accounts_userprofile', (
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='profile', unique=True, to=orm['auth.User'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reputation', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'accounts', ['UserProfile'])

        # Adding model 'Member'
        db.create_table(u'accounts_member', (
            ('slack_budget', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('semester', self.gf('django.db.models.fields.related.ForeignKey')(related_name='members', to=orm['chunks.Semester'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='membership', to=orm['auth.User'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'accounts', ['Member'])

        # Adding model 'Extension'
        db.create_table(u'accounts_extension', (
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='extensions', to=orm['auth.User'])),
            ('slack_used', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='extensions', to=orm['chunks.Milestone'])),
        ))
        db.send_create_signal(u'accounts', ['Extension'])


    models = {
        
    }

    complete_apps = ['accounts']