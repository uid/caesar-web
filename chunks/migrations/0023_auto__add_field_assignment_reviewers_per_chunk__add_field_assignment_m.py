# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Assignment.reviewers_per_chunk'
        db.add_column(u'assignments', 'reviewers_per_chunk', self.gf('django.db.models.fields.IntegerField')(default=2), keep_default=False)

        # Adding field 'Assignment.min_student_lines'
        db.add_column(u'assignments', 'min_student_lines', self.gf('django.db.models.fields.IntegerField')(default=30), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Assignment.reviewers_per_chunk'
        db.delete_column(u'assignments', 'reviewers_per_chunk')

        # Deleting field 'Assignment.min_student_lines'
        db.delete_column(u'assignments', 'min_student_lines')


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
            'alum_count': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'alum_count_default': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'alums': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'alums_default': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'chunks_to_assign': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'code_review_end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duedate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_extension': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'min_student_lines': ('django.db.models.fields.IntegerField', [], {'default': '30'}),
            'multiplier': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'reviewers_per_chunk': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'semester': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'staff': ('django.db.models.fields.IntegerField', [], {'default': '15'}),
            'staff_count': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'staff_count_default': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'staff_default': ('django.db.models.fields.IntegerField', [], {'default': '15'}),
            'student_count': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'student_count_default': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'students': ('django.db.models.fields.IntegerField', [], {'default': '199'}),
            'students_default': ('django.db.models.fields.IntegerField', [], {'default': '199'})
        },
        'chunks.chunk': {
            'Meta': {'object_name': 'Chunk', 'db_table': "u'chunks'"},
            'class_type': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'cluster_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.IntegerField', [], {}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'chunks'", 'to': "orm['chunks.File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'staff_portion': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'start': ('django.db.models.fields.IntegerField', [], {})
        },
        'chunks.chunkprofile': {
            'Meta': {'object_name': 'ChunkProfile'},
            'chunk': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['chunks.Chunk']"}),
            'comment_words': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'for_nesting_depth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'if_nesting_depth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'return_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'static_comments': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'student_lines': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'synchronized_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'valid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'viable_comments': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'chunks.file': {
            'Meta': {'unique_together': "(('path', 'submission'),)", 'object_name': 'File', 'db_table': "u'files'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['chunks.Submission']"})
        },
        'chunks.fingerprint': {
            'Meta': {'unique_together': "(('chunk', 'position'),)", 'object_name': 'Fingerprint', 'db_table': "u'fingerprints'"},
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fingerprints'", 'to': "orm['chunks.Chunk']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'value': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        'chunks.staffmarker': {
            'Meta': {'object_name': 'StaffMarker'},
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'staffmarkers'", 'to': "orm['chunks.Chunk']"}),
            'end_line': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_line': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'chunks.submission': {
            'Meta': {'object_name': 'Submission', 'db_table': "u'submissions'"},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['chunks.Assignment']"}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': "orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duedate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'revision_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
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
