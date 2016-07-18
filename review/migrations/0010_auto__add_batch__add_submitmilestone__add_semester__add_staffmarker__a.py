# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Batch'
        db.create_table(u'chunks_batch', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'review', ['Batch'])

        # Adding model 'SubmitMilestone'
        db.create_table(u'chunks_submitmilestone', (
            (u'milestone_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['review.Milestone'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'review', ['SubmitMilestone'])

        # Adding model 'Semester'
        db.create_table(u'chunks_semester', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.related.ForeignKey')(related_name='semesters', to=orm['review.Subject'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=140, blank=True)),
            ('about', self.gf('review.fields.MarkdownTextField')(blank=True)),
            ('semester', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('is_current_semester', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('about_html', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'review', ['Semester'])

        # Adding model 'StaffMarker'
        db.create_table(u'chunks_staffmarker', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chunk', self.gf('django.db.models.fields.related.ForeignKey')(related_name='staffmarkers', to=orm['review.Chunk'])),
            ('start_line', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('end_line', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'review', ['StaffMarker'])

        # Adding model 'ReviewMilestone'
        db.create_table(u'chunks_reviewmilestone', (
            (u'milestone_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['review.Milestone'], unique=True, primary_key=True)),
            ('reviewers_per_chunk', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('min_student_lines', self.gf('django.db.models.fields.IntegerField')(default=30)),
            ('submit_milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='review_milestone', to=orm['review.SubmitMilestone'])),
            ('chunks_to_assign', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('chunks_to_exclude', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('student_count', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('student_count_default', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('alum_count', self.gf('django.db.models.fields.IntegerField')(default=3)),
            ('alum_count_default', self.gf('django.db.models.fields.IntegerField')(default=3)),
            ('staff_count', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('staff_count_default', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('students', self.gf('django.db.models.fields.IntegerField')(default=199)),
            ('students_default', self.gf('django.db.models.fields.IntegerField')(default=199)),
            ('alums', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('alums_default', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('staff', self.gf('django.db.models.fields.IntegerField')(default=15)),
            ('staff_default', self.gf('django.db.models.fields.IntegerField')(default=15)),
        ))
        db.send_create_signal(u'review', ['ReviewMilestone'])

        # Adding model 'Milestone'
        db.create_table(u'chunks_milestone', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assignment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='milestones', to=orm['review.Assignment'])),
            ('assigned_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('duedate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('max_extension', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal(u'review', ['Milestone'])

        # Adding model 'Subject'
        db.create_table(u'chunks_subject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'review', ['Subject'])

        # Adding model 'File'
        db.create_table(u'files', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('data', self.gf('django.db.models.fields.TextField')()),
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='files', to=orm['review.Submission'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'review', ['File'])

        # Adding unique constraint on 'File', fields ['path', 'submission']
        db.create_unique(u'files', ['path', 'submission_id'])

        # Adding model 'Assignment'
        db.create_table(u'assignments', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('semester', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignments', null=True, to=orm['review.Semester'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'review', ['Assignment'])

        # Adding model 'Submission'
        db.create_table(u'submissions', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('revision', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('revision_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['review.SubmitMilestone'])),
            ('batch', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='submissions', null=True, to=orm['review.Batch'])),
        ))
        db.send_create_signal(u'review', ['Submission'])

        # Adding M2M table for field authors on 'Submission'
        m2m_table_name = db.shorten_name(u'submissions_authors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('submission', models.ForeignKey(orm[u'review.submission'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['submission_id', 'user_id'])

        # Adding model 'Chunk'
        db.create_table(u'chunks', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.related.ForeignKey')(related_name='chunks', to=orm['review.File'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('start', self.gf('django.db.models.fields.IntegerField')()),
            ('end', self.gf('django.db.models.fields.IntegerField')()),
            ('cluster_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('class_type', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('staff_portion', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('student_lines', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('chunk_info', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'review', ['Chunk'])


        # Changing field 'ChunkReview.chunk'
        db.alter_column('tasks_chunkreview', 'chunk_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['review.Chunk']))

        # Changing field 'Notification.submission'
        db.alter_column('notifications_notification', 'submission_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['review.Submission']))

        # Changing field 'Member.semester'
        db.alter_column('accounts_member', 'semester_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['review.Semester']))

        # Changing field 'Task.submission'
        db.alter_column('tasks_task', 'submission_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['review.Submission']))

        # Changing field 'Task.chunk'
        db.alter_column('tasks_task', 'chunk_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['review.Chunk']))

        # Changing field 'Task.milestone'
        db.alter_column('tasks_task', 'milestone_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['review.ReviewMilestone']))

        # Changing field 'Comment.chunk'
        db.alter_column(u'review_comment', 'chunk_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['review.Chunk']))

        # Changing field 'Comment.batch'
        db.alter_column(u'review_comment', 'batch_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['review.Batch']))

        # Changing field 'Extension.milestone'
        db.alter_column('accounts_extension', 'milestone_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['review.Milestone']))

    def backwards(self, orm):
        # # Removing unique constraint on 'File', fields ['path', 'submission']
        # db.delete_unique(u'files', ['path', 'submission_id'])

        # # Deleting model 'Batch'
        # db.delete_table(u'chunks_batch')

        # # Deleting model 'SubmitMilestone'
        # db.delete_table(u'chunks_submitmilestone')

        # # Deleting model 'Semester'
        # db.delete_table(u'chunks_semester')

        # # Deleting model 'StaffMarker'
        # db.delete_table(u'chunks_staffmarker')

        # # Deleting model 'ReviewMilestone'
        # db.delete_table(u'chunks_reviewmilestone')

        # # Deleting model 'Milestone'
        # db.delete_table(u'chunks_milestone')

        # # Deleting model 'Subject'
        # db.delete_table(u'chunks_subject')

        # # Deleting model 'File'
        # db.delete_table(u'files')

        # # Deleting model 'Assignment'
        # db.delete_table(u'assignments')

        # # Deleting model 'Submission'
        # db.delete_table(u'submissions')

        # # Removing M2M table for field authors on 'Submission'
        # db.delete_table(db.shorten_name(u'submissions_authors'))

        # # Deleting model 'Chunk'
        # db.delete_table(u'chunks')


        # # Changing field 'ChunkReview.chunk'
        # db.alter_column('tasks_chunkreview', 'chunk_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['chunks.Chunk']))

        # # Changing field 'Notification.submission'
        # db.alter_column('notifications_notification', 'submission_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['chunks.Submission']))

        # # Changing field 'Member.semester'
        # db.alter_column('accounts_member', 'semester_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chunks.Semester']))

        # # Changing field 'Task.submission'
        # db.alter_column('tasks_task', 'submission_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['chunks.Submission']))

        # # Changing field 'Task.chunk'
        # db.alter_column('tasks_task', 'chunk_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['chunks.Chunk']))

        # # Changing field 'Task.milestone'
        # db.alter_column('tasks_task', 'milestone_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chunks.ReviewMilestone']))

        # # Changing field 'Comment.chunk'
        # db.alter_column(u'review_comment', 'chunk_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chunks.Chunk']))

        # # Changing field 'Comment.batch'
        # db.alter_column(u'review_comment', 'batch_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['chunks.Batch']))

        # # Changing field 'Extension.milestone'
        # db.alter_column('accounts_extension', 'milestone_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chunks.Milestone']))

        # don't delete anything, because we're just moving these models back to chunks app
        pass

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'review.assignment': {
            'Meta': {'object_name': 'Assignment', 'db_table': "u'assignments'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'semester': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'null': 'True', 'to': u"orm['review.Semester']"})
        },
        u'review.batch': {
            'Meta': {'object_name': 'Batch'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'review.chunk': {
            'Meta': {'object_name': 'Chunk', 'db_table': "u'chunks'"},
            'chunk_info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'class_type': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'cluster_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.IntegerField', [], {}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'chunks'", 'to': u"orm['review.File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'staff_portion': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'start': ('django.db.models.fields.IntegerField', [], {}),
            'student_lines': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'review.chunkreview': {
            'Meta': {'object_name': 'ChunkReview', 'db_table': "'tasks_chunkreview'"},
            'chunk': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'chunk_review'", 'unique': 'True', 'null': 'True', 'to': u"orm['review.Chunk']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'staff_reviewers': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'student_or_alum_reviewers': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'review.comment': {
            'Meta': {'ordering': "['start', '-end', 'thread_id', 'created']", 'object_name': 'Comment'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['auth.User']"}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'comments'", 'null': 'True', 'to': u"orm['review.Batch']"}),
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['review.Chunk']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'downvote_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'edited': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_comments'", 'null': 'True', 'to': u"orm['review.Comment']"}),
            'similar_comment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'similar_comments'", 'null': 'True', 'to': u"orm['review.Comment']"}),
            'start': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'thread_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'upvote_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'review.extension': {
            'Meta': {'object_name': 'Extension', 'db_table': "'accounts_extension'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'extensions'", 'to': u"orm['review.Milestone']"}),
            'slack_used': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'extensions'", 'to': u"orm['auth.User']"})
        },
        u'review.file': {
            'Meta': {'unique_together': "(('path', 'submission'),)", 'object_name': 'File', 'db_table': "u'files'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': u"orm['review.Submission']"})
        },
        u'review.member': {
            'Meta': {'object_name': 'Member', 'db_table': "'accounts_member'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'semester': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'members'", 'to': u"orm['review.Semester']"}),
            'slack_budget': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'membership'", 'to': u"orm['auth.User']"})
        },
        u'review.milestone': {
            'Meta': {'object_name': 'Milestone', 'db_table': "u'chunks_milestone'"},
            'assigned_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'milestones'", 'to': u"orm['review.Assignment']"}),
            'duedate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_extension': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        u'review.notification': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Notification', 'db_table': "'notifications_notification'"},
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'notifications'", 'null': 'True', 'to': u"orm['review.Comment']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notifications'", 'to': u"orm['auth.User']"}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'notifications'", 'null': 'True', 'to': u"orm['review.Submission']"})
        },
        u'review.reviewmilestone': {
            'Meta': {'object_name': 'ReviewMilestone', 'db_table': "u'chunks_reviewmilestone'", '_ormbases': [u'review.Milestone']},
            'alum_count': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'alum_count_default': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'alums': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'alums_default': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'chunks_to_assign': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'chunks_to_exclude': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'milestone_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['review.Milestone']", 'unique': 'True', 'primary_key': 'True'}),
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
            'submit_milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'review_milestone'", 'to': u"orm['review.SubmitMilestone']"})
        },
        u'review.semester': {
            'Meta': {'object_name': 'Semester', 'db_table': "u'chunks_semester'"},
            'about': ('review.fields.MarkdownTextField', [], {'blank': 'True'}),
            'about_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '140', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_current_semester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'semester': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'semesters'", 'to': u"orm['review.Subject']"})
        },
        u'review.staffmarker': {
            'Meta': {'object_name': 'StaffMarker', 'db_table': "u'chunks_staffmarker'"},
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'staffmarkers'", 'to': u"orm['review.Chunk']"}),
            'end_line': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_line': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'review.subject': {
            'Meta': {'object_name': 'Subject', 'db_table': "u'chunks_subject'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'review.submission': {
            'Meta': {'object_name': 'Submission', 'db_table': "u'submissions'"},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': u"orm['review.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': u"orm['review.SubmitMilestone']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'revision_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'review.submitmilestone': {
            'Meta': {'object_name': 'SubmitMilestone', 'db_table': "u'chunks_submitmilestone'", '_ormbases': [u'review.Milestone']},
            u'milestone_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['review.Milestone']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'review.task': {
            'Meta': {'unique_together': "(('chunk', 'reviewer'),)", 'object_name': 'Task', 'db_table': "'tasks_task'"},
            'chunk': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'tasks'", 'null': 'True', 'to': u"orm['review.Chunk']"}),
            'chunk_review': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'tasks'", 'null': 'True', 'to': u"orm['review.ChunkReview']"}),
            'completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': u"orm['review.ReviewMilestone']"}),
            'opened': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'tasks'", 'null': 'True', 'to': u"orm['review.Submission']"})
        },
        u'review.userprofile': {
            'Meta': {'object_name': 'UserProfile', 'db_table': "'accounts_userprofile'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reputation': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'review.vote': {
            'Meta': {'unique_together': "(('comment', 'author'),)", 'object_name': 'Vote'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': u"orm['auth.User']"}),
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': u"orm['review.Comment']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.SmallIntegerField', [], {})
        }
    }

    complete_apps = ['review']