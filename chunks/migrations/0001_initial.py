# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Assignment'
        db.create_table(u'assignments', (
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('chunks', ['Assignment'])

        # Adding model 'Submission'
        db.create_table(u'submissions', (
            ('assignment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chunks.Assignment'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('chunks', ['Submission'])

        # Adding model 'File'
        db.create_table(u'files', (
            ('path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('data', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chunks.Submission'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('chunks', ['File'])

        # Adding unique constraint on 'File', fields ['path', 'submission']
        db.create_unique(u'files', ['path', 'submission_id'])

        # Adding model 'Chunk'
        db.create_table(u'chunks', (
            ('start', self.gf('django.db.models.fields.IntegerField')()),
            ('end', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chunks.File'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('chunks', ['Chunk'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Assignment'
        db.delete_table(u'assignments')

        # Deleting model 'Submission'
        db.delete_table(u'submissions')

        # Deleting model 'File'
        db.delete_table(u'files')

        # Removing unique constraint on 'File', fields ['path', 'submission']
        db.delete_unique(u'files', ['path', 'submission_id'])

        # Deleting model 'Chunk'
        db.delete_table(u'chunks')
    
    
    models = {
        'chunks.assignment': {
            'Meta': {'object_name': 'Assignment', 'db_table': "u'assignments'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'chunks.chunk': {
            'Meta': {'object_name': 'Chunk', 'db_table': "u'chunks'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'end': ('django.db.models.fields.IntegerField', [], {}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chunks.File']"}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'start': ('django.db.models.fields.IntegerField', [], {})
        },
        'chunks.file': {
            'Meta': {'unique_together': "(('path', 'submission'),)", 'object_name': 'File', 'db_table': "u'files'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chunks.Submission']"})
        },
        'chunks.submission': {
            'Meta': {'object_name': 'Submission', 'db_table': "u'submissions'"},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chunks.Assignment']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }
    
    complete_apps = ['chunks']
