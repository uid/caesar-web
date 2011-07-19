# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Fingerprint'
        db.create_table(u'fingerprints', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chunk', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fingerprints', to=orm['chunks.Chunk'])),
            ('value', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('position', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('chunks', ['Fingerprint'])

        # Adding unique constraint on 'Fingerprint', fields ['chunk', 'position']
        db.create_unique(u'fingerprints', ['chunk_id', 'position'])

        # Adding field 'Submission.author'
        db.add_column(u'submissions', 'author', self.gf('django.db.models.fields.related.ForeignKey')(default=8, to=orm['auth.User']), keep_default=False)

        # Adding field 'Chunk.name'
        db.add_column(u'chunks', 'name', self.gf('django.db.models.fields.CharField')(default='DEFAULT', max_length=200), keep_default=False)

        # Adding field 'Chunk.modified'
        db.add_column(u'chunks', 'modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.date(2011, 7, 18)), keep_default=False)


    def backwards(self, orm):
        
        # Removing unique constraint on 'Fingerprint', fields ['chunk', 'position']
        db.delete_unique(u'fingerprints', ['chunk_id', 'position'])

        # Deleting model 'Fingerprint'
        db.delete_table(u'fingerprints')

        # Deleting field 'Submission.author'
        db.delete_column(u'submissions', 'author_id')

        # Deleting field 'Chunk.name'
        db.delete_column(u'chunks', 'name')

        # Deleting field 'Chunk.modified'
        db.delete_column(u'chunks', 'modified')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'chunks.assignment': {
            'Meta': {'object_name': 'Assignment', 'db_table': "u'assignments'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'chunks.chunk': {
            'Meta': {'object_name': 'Chunk', 'db_table': "u'chunks'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'end': ('django.db.models.fields.IntegerField', [], {}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chunks.File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'start': ('django.db.models.fields.IntegerField', [], {})
        },
        'chunks.file': {
            'Meta': {'unique_together': "(('path', 'submission'),)", 'object_name': 'File', 'db_table': "u'files'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chunks.Submission']"})
        },
        'chunks.fingerprint': {
            'Meta': {'unique_together': "(('chunk', 'position'),)", 'object_name': 'Fingerprint', 'db_table': "u'fingerprints'"},
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fingerprints'", 'to': "orm['chunks.Chunk']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'value': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        'chunks.submission': {
            'Meta': {'object_name': 'Submission', 'db_table': "u'submissions'"},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chunks.Assignment']"}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['chunks']
