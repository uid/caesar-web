# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # # Removing unique constraint on 'File', fields ['path', 'submission']
        # db.delete_unique(u'files', ['path', 'submission_id'])

        # # Deleting model 'Batch'
        # db.delete_table(u'chunks_batch')

        # # Deleting model 'Subject'
        # db.delete_table(u'chunks_subject')

        # # Deleting model 'SubmitMilestone'
        # db.delete_table(u'chunks_submitmilestone')

        # # Deleting model 'File'
        # db.delete_table(u'files')

        # # Deleting model 'Milestone'
        # db.delete_table(u'chunks_milestone')

        # # Deleting model 'Submission'
        # db.delete_table(u'submissions')

        # # Removing M2M table for field authors on 'Submission'
        # db.delete_table(db.shorten_name(u'submissions_authors'))

        # # Deleting model 'StaffMarker'
        # db.delete_table(u'chunks_staffmarker')

        # # Deleting model 'Assignment'
        # db.delete_table(u'assignments')

        # # Deleting model 'Chunk'
        # db.delete_table(u'chunks')

        # # Deleting model 'ReviewMilestone'
        # db.delete_table(u'chunks_reviewmilestone')

        # # Deleting model 'Semester'
        # db.delete_table(u'chunks_semester')

        # don't delete, because we're just moving the models to the review app
        pass

    def backwards(self, orm):
        # Adding model 'Batch'
        db.create_table(u'chunks_batch', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'chunks', ['Batch'])

        # Adding model 'Subject'
        db.create_table(u'chunks_subject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'chunks', ['Subject'])

        # Adding model 'SubmitMilestone'
        db.create_table(u'chunks_submitmilestone', (
            (u'milestone_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['chunks.Milestone'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'chunks', ['SubmitMilestone'])

        # Adding model 'File'
        db.create_table(u'files', (
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='files', to=orm['chunks.Submission'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('data', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'chunks', ['File'])

        # Adding unique constraint on 'File', fields ['path', 'submission']
        db.create_unique(u'files', ['path', 'submission_id'])

        # Adding model 'Milestone'
        db.create_table(u'chunks_milestone', (
            ('max_extension', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('assignment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='milestones', to=orm['chunks.Assignment'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('duedate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('assigned_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'chunks', ['Milestone'])

        # Adding model 'Submission'
        db.create_table(u'submissions', (
            ('revision_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['chunks.SubmitMilestone'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('revision', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('batch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', null=True, to=orm['chunks.Batch'], blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'chunks', ['Submission'])

        # Adding M2M table for field authors on 'Submission'
        m2m_table_name = db.shorten_name(u'submissions_authors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('submission', models.ForeignKey(orm[u'chunks.submission'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['submission_id', 'user_id'])

        # Adding model 'StaffMarker'
        db.create_table(u'chunks_staffmarker', (
            ('chunk', self.gf('django.db.models.fields.related.ForeignKey')(related_name='staffmarkers', to=orm['chunks.Chunk'])),
            ('end_line', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('start_line', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'chunks', ['StaffMarker'])

        # Adding model 'Assignment'
        db.create_table(u'assignments', (
            ('semester', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignments', null=True, to=orm['chunks.Semester'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'chunks', ['Assignment'])

        # Adding model 'Chunk'
        db.create_table(u'chunks', (
            ('class_type', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('cluster_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('file', self.gf('django.db.models.fields.related.ForeignKey')(related_name='chunks', to=orm['chunks.File'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('end', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('student_lines', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('start', self.gf('django.db.models.fields.IntegerField')()),
            ('staff_portion', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('chunk_info', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'chunks', ['Chunk'])

        # Adding model 'ReviewMilestone'
        db.create_table(u'chunks_reviewmilestone', (
            ('chunks_to_exclude', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('min_student_lines', self.gf('django.db.models.fields.IntegerField')(default=30)),
            ('students_default', self.gf('django.db.models.fields.IntegerField')(default=199)),
            ('staff_count_default', self.gf('django.db.models.fields.IntegerField')(default=10)),
            (u'milestone_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['chunks.Milestone'], unique=True, primary_key=True)),
            ('staff_default', self.gf('django.db.models.fields.IntegerField')(default=15)),
            ('student_count', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('submit_milestone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='review_milestone', to=orm['chunks.SubmitMilestone'])),
            ('alums_default', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('student_count_default', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('staff_count', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('students', self.gf('django.db.models.fields.IntegerField')(default=199)),
            ('chunks_to_assign', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('reviewers_per_chunk', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('alums', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('staff', self.gf('django.db.models.fields.IntegerField')(default=15)),
            ('alum_count_default', self.gf('django.db.models.fields.IntegerField')(default=3)),
            ('alum_count', self.gf('django.db.models.fields.IntegerField')(default=3)),
        ))
        db.send_create_signal(u'chunks', ['ReviewMilestone'])

        # Adding model 'Semester'
        db.create_table(u'chunks_semester', (
            ('about', self.gf('review.fields.MarkdownTextField')(blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=140, blank=True)),
            ('semester', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('about_html', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('is_current_semester', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.related.ForeignKey')(related_name='semesters', to=orm['chunks.Subject'])),
        ))
        db.send_create_signal(u'chunks', ['Semester'])


    models = {
        
    }

    complete_apps = ['chunks']