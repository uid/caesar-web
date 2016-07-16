# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Article', fields ['slug', 'parent']
        db.delete_unique(u'simplewiki_article', ['slug', 'parent_id'])

        # Deleting model 'Permission'
        db.delete_table(u'simplewiki_permission')

        # Removing M2M table for field can_read on 'Permission'
        db.delete_table(db.shorten_name(u'simplewiki_permission_can_read'))

        # Removing M2M table for field can_write on 'Permission'
        db.delete_table(db.shorten_name(u'simplewiki_permission_can_write'))

        # Deleting model 'ArticleAttachment'
        db.delete_table(u'simplewiki_articleattachment')

        # Deleting model 'Revision'
        db.delete_table(u'simplewiki_revision')

        # Deleting model 'Article'
        db.delete_table(u'simplewiki_article')

        # Removing M2M table for field related on 'Article'
        db.delete_table(db.shorten_name(u'simplewiki_article_related'))

        from django.contrib.contenttypes.models import ContentType
        ContentType.objects.filter(app_label='simpewiki').delete()


    def backwards(self, orm):
        # Adding model 'Permission'
        db.create_table(u'simplewiki_permission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('permission_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'simplewiki', ['Permission'])

        # Adding M2M table for field can_read on 'Permission'
        m2m_table_name = db.shorten_name(u'simplewiki_permission_can_read')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm[u'simplewiki.permission'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['permission_id', 'user_id'])

        # Adding M2M table for field can_write on 'Permission'
        m2m_table_name = db.shorten_name(u'simplewiki_permission_can_write')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm[u'simplewiki.permission'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['permission_id', 'user_id'])

        # Adding model 'ArticleAttachment'
        db.create_table(u'simplewiki_articleattachment', (
            ('uploaded_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=255)),
            ('uploaded_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('article', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Article'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'simplewiki', ['ArticleAttachment'])

        # Adding model 'Revision'
        db.create_table(u'simplewiki_revision', (
            ('contents_parsed', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('revision_text', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('revision_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('revision_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='wiki_revision_user', null=True, to=orm['auth.User'], blank=True)),
            ('article', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Article'])),
            ('counter', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('previous_revision', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Revision'], null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contents', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'simplewiki', ['Revision'])

        # Adding model 'Article'
        db.create_table(u'simplewiki_article', (
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Article'], null=True, blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=1, blank=True)),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=1, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=100, blank=True)),
            ('permissions', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Permission'], null=True, blank=True)),
            ('locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('current_revision', self.gf('django.db.models.fields.related.OneToOneField')(related_name='current_rev', unique=True, null=True, to=orm['simplewiki.Revision'], blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'simplewiki', ['Article'])

        # Adding M2M table for field related on 'Article'
        m2m_table_name = db.shorten_name(u'simplewiki_article_related')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_article', models.ForeignKey(orm[u'simplewiki.article'], null=False)),
            ('to_article', models.ForeignKey(orm[u'simplewiki.article'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_article_id', 'to_article_id'])

        # Adding unique constraint on 'Article', fields ['slug', 'parent']
        db.create_unique(u'simplewiki_article', ['slug', 'parent_id'])


    models = {
        
    }

    complete_apps = ['simplewiki']