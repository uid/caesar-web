# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    needed_by = (
        ("chunks", "0034_auto__del_field_submission_assignment__del_field_submission_duedate__d"),
    )

    def forwards(self, orm):
        # Deleting field 'Extension.assignment'
        db.delete_column('accounts_extension', 'assignment_id')


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Extension.assignment'
        raise RuntimeError("Cannot reverse this migration. 'Extension.assignment' and its values cannot be restored.")

    models = {
        'accounts.extension': {
            'Meta': {'object_name': 'Extension'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'extensions'", 'to': "orm['chunks.Milestone']"}),
            'slack_used': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'extensions'", 'to': "orm['auth.User']"})
        },
        'accounts.member': {
            'Meta': {'object_name': 'Member'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'semester': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'members'", 'to': "orm['chunks.Semester']"}),
            'slack_budget': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'membership'", 'to': "orm['auth.User']"})
        },
        'accounts.token': {
            'Meta': {'object_name': 'Token'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'expire': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'accounts.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'about': ('accounts.fields.MarkdownTextField', [], {'blank': 'True'}),
            'about_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'assigned_chunks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'reviewers'", 'symmetrical': 'False', 'through': "orm['tasks.Task']", 'to': "orm['chunks.Chunk']"}),
            'class_year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.CharField', [], {'default': "'MIT'", 'max_length': '100', 'blank': 'True'}),
            'github': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linkedin': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'reputation': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'token': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'invited'", 'null': 'True', 'to': "orm['accounts.Token']"}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
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
            'is_live': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'max_extension': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'min_student_lines': ('django.db.models.fields.IntegerField', [], {'default': '30'}),
            'multiplier': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'reviewers_per_chunk': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'semester': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'null': 'True', 'to': "orm['chunks.Semester']"}),
            'staff': ('django.db.models.fields.IntegerField', [], {'default': '15'}),
            'staff_count': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'staff_count_default': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'staff_default': ('django.db.models.fields.IntegerField', [], {'default': '15'}),
            'student_count': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'student_count_default': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'students': ('django.db.models.fields.IntegerField', [], {'default': '199'}),
            'students_default': ('django.db.models.fields.IntegerField', [], {'default': '199'})
        },
        'chunks.batch': {
            'Meta': {'object_name': 'Batch'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'batches'", 'to': "orm['chunks.Assignment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_live': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'files'", 'null': 'True', 'to': "orm['chunks.Batch']"}),
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
            'chunks_to_assign': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'milestone_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['chunks.Milestone']", 'unique': 'True', 'primary_key': 'True'}),
            'min_student_lines': ('django.db.models.fields.IntegerField', [], {'default': '30'}),
            'reviewers_per_chunk': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'submit_milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'review_milestones'", 'to': "orm['chunks.SubmitMilestone']"})
        },
        'chunks.semester': {
            'Meta': {'object_name': 'Semester'},
            'about': ('accounts.fields.MarkdownTextField', [], {'blank': 'True'}),
            'about_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '140', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_current_semester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'semester': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'semesters'", 'to': "orm['chunks.Subject']"})
        },
        'chunks.subject': {
            'Meta': {'object_name': 'Subject'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'chunks.submission': {
            'Meta': {'object_name': 'Submission', 'db_table': "u'submissions'"},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['chunks.Assignment']"}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': "orm['auth.User']"}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': "orm['chunks.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duedate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
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
        },
        'tasks.task': {
            'Meta': {'unique_together': "(('chunk', 'reviewer'),)", 'object_name': 'Task'},
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['chunks.Chunk']"}),
            'completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['chunks.ReviewMilestone']"}),
            'opened': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['accounts.UserProfile']"}),
            'started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'})
        }
    }

    complete_apps = ['accounts']