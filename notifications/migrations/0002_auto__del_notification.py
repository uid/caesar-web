# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Moved model 'Notification' to review
        #db.delete_table(u'notifications_notification')
        pass

    def backwards(self, orm):
        # Adding model 'Notification'
        db.create_table(u'notifications_notification', (
            ('comment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='notifications', null=True, to=orm['review.Comment'], blank=True)),
            ('reason', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='notifications', null=True, to=orm['chunks.Submission'], blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='notifications', to=orm['auth.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email_sent', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('notifications', ['Notification'])


    models = {
        
    }

    complete_apps = ['notifications']