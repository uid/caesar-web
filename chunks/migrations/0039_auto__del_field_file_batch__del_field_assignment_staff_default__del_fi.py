# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'File.batch'
        db.delete_column(u'files', 'batch_id')

        # Deleting field 'Assignment.staff_default'
        db.delete_column(u'assignments', 'staff_default')

        # Deleting field 'Assignment.students_default'
        db.delete_column(u'assignments', 'students_default')

        # Deleting field 'Assignment.staff_count_default'
        db.delete_column(u'assignments', 'staff_count_default')

        # Deleting field 'Assignment.student_count'
        db.delete_column(u'assignments', 'student_count')

        # Deleting field 'Assignment.students'
        db.delete_column(u'assignments', 'students')

        # Deleting field 'Assignment.staff_count'
        db.delete_column(u'assignments', 'staff_count')

        # Deleting field 'Assignment.alums_default'
        db.delete_column(u'assignments', 'alums_default')

        # Deleting field 'Assignment.student_count_default'
        db.delete_column(u'assignments', 'student_count_default')

        # Deleting field 'Assignment.alums'
        db.delete_column(u'assignments', 'alums')

        # Deleting field 'Assignment.staff'
        db.delete_column(u'assignments', 'staff')

        # Deleting field 'Assignment.alum_count_default'
        db.delete_column(u'assignments', 'alum_count_default')

        # Deleting field 'Assignment.alum_count'
        db.delete_column(u'assignments', 'alum_count')


    def backwards(self, orm):
        # Adding field 'File.batch'
        db.add_column(u'files', 'batch',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='files', null=True, to=orm['chunks.Batch'], blank=True),
                      keep_default=False)

        # Adding field 'Assignment.staff_default'
        db.add_column(u'assignments', 'staff_default',
                      self.gf('django.db.models.fields.IntegerField')(default=15),
                      keep_default=False)

        # Adding field 'Assignment.students_default'
        db.add_column(u'assignments', 'students_default',
                      self.gf('django.db.models.fields.IntegerField')(default=199),
                      keep_default=False)

        # Adding field 'Assignment.staff_count_default'
        db.add_column(u'assignments', 'staff_count_default',
                      self.gf('django.db.models.fields.IntegerField')(default=10),
                      keep_default=False)

        # Adding field 'Assignment.student_count'
        db.add_column(u'assignments', 'student_count',
                      self.gf('django.db.models.fields.IntegerField')(default=5),
                      keep_default=False)

        # Adding field 'Assignment.students'
        db.add_column(u'assignments', 'students',
                      self.gf('django.db.models.fields.IntegerField')(default=199),
                      keep_default=False)

        # Adding field 'Assignment.staff_count'
        db.add_column(u'assignments', 'staff_count',
                      self.gf('django.db.models.fields.IntegerField')(default=10),
                      keep_default=False)

        # Adding field 'Assignment.alums_default'
        db.add_column(u'assignments', 'alums_default',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Adding field 'Assignment.student_count_default'
        db.add_column(u'assignments', 'student_count_default',
                      self.gf('django.db.models.fields.IntegerField')(default=5),
                      keep_default=False)

        # Adding field 'Assignment.alums'
        db.add_column(u'assignments', 'alums',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Adding field 'Assignment.staff'
        db.add_column(u'assignments', 'staff',
                      self.gf('django.db.models.fields.IntegerField')(default=15),
                      keep_default=False)

        # Adding field 'Assignment.alum_count_default'
        db.add_column(u'assignments', 'alum_count_default',
                      self.gf('django.db.models.fields.IntegerField')(default=3),
                      keep_default=False)

        # Adding field 'Assignment.alum_count'
        db.add_column(u'assignments', 'alum_count',
                      self.gf('django.db.models.fields.IntegerField')(default=3),
                      keep_default=False)


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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_live': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'semester': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'null': 'True', 'to': "orm['chunks.Semester']"})
        },
        'chunks.batch': {
            'Meta': {'object_name': 'Batch'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_live': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'chunks.chunk': {
            'Meta': {'object_name': 'Chunk', 'db_table': "u'chunks'"},
            'chunk_info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'class_type': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'cluster_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.IntegerField', [], {}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'chunks'", 'to': "orm['chunks.File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'staff_portion': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'start': ('django.db.models.fields.IntegerField', [], {}),
            'student_lines': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'chunks.file': {
            'Meta': {'unique_together': "(('path', 'submission'),)", 'object_name': 'File', 'db_table': "u'files'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['chunks.Submission']"})
        },
        'chunks.milestone': {
            'Meta': {'object_name': 'Milestone'},
            'assigned_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'milestones'", 'to': "orm['chunks.Assignment']"}),
            'duedate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_extension': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'chunks.reviewmilestone': {
            'Meta': {'object_name': 'ReviewMilestone', '_ormbases': ['chunks.Milestone']},
            'alum_count': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'alum_count_default': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'alums': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'alums_default': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'chunks_to_assign': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'milestone_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['chunks.Milestone']", 'unique': 'True', 'primary_key': 'True'}),
            'min_student_lines': ('django.db.models.fields.IntegerField', [], {'default': '30'}),
            'reviewers_per_chunk': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'staff': ('django.db.models.fields.IntegerField', [], {'default': '15'}),
            'staff_count': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'staff_count_default': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'staff_default': ('django.db.models.fields.IntegerField', [], {'default': '15'}),
            'student_count': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'student_count_default': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'students': ('django.db.models.fields.IntegerField', [], {'default': '199'}),
            'students_default': ('django.db.models.fields.IntegerField', [], {'default': '199'}),
            'submit_milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'review_milestones'", 'to': "orm['chunks.SubmitMilestone']"})
        },
        'chunks.semester': {
            'Meta': {'object_name': 'Semester'},
            'about': ('review.fields.MarkdownTextField', [], {'blank': 'True'}),
            'about_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '140', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_current_semester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'semester': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'semesters'", 'to': "orm['chunks.Subject']"})
        },
        'chunks.staffmarker': {
            'Meta': {'object_name': 'StaffMarker'},
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'staffmarkers'", 'to': "orm['chunks.Chunk']"}),
            'end_line': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_line': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'chunks.subject': {
            'Meta': {'object_name': 'Subject'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'chunks.submission': {
            'Meta': {'object_name': 'Submission', 'db_table': "u'submissions'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': "orm['auth.User']"}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': "orm['chunks.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['chunks.SubmitMilestone']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'revision_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'chunks.submitmilestone': {
            'Meta': {'object_name': 'SubmitMilestone', '_ormbases': ['chunks.Milestone']},
            'milestone_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['chunks.Milestone']", 'unique': 'True', 'primary_key': 'True'})
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