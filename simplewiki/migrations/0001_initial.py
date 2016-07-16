# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Article'
        db.create_table(u'simplewiki_article', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=100, blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=1, blank=True)),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=1, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Article'], null=True, blank=True)),
            ('locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('permissions', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Permission'], null=True, blank=True)),
            ('current_revision', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='current_rev', unique=True, null=True, to=orm['simplewiki.Revision'])),
        ))
        db.send_create_signal(u'simplewiki', ['Article'])

        # Adding unique constraint on 'Article', fields ['slug', 'parent']
        db.create_unique(u'simplewiki_article', ['slug', 'parent_id'])

        # Adding M2M table for field related on 'Article'
        m2m_table_name = db.shorten_name(u'simplewiki_article_related')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_article', models.ForeignKey(orm[u'simplewiki.article'], null=False)),
            ('to_article', models.ForeignKey(orm[u'simplewiki.article'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_article_id', 'to_article_id'])

        # Adding model 'ArticleAttachment'
        db.create_table(u'simplewiki_articleattachment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('article', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Article'])),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=255)),
            ('uploaded_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('uploaded_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'simplewiki', ['ArticleAttachment'])

        # Adding model 'Revision'
        db.create_table(u'simplewiki_revision', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('article', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Article'])),
            ('revision_text', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('revision_user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='wiki_revision_user', null=True, to=orm['auth.User'])),
            ('revision_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('contents', self.gf('django.db.models.fields.TextField')()),
            ('contents_parsed', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('counter', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('previous_revision', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simplewiki.Revision'], null=True, blank=True)),
        ))
        db.send_create_signal(u'simplewiki', ['Revision'])

        # Adding model 'Permission'
        db.create_table(u'simplewiki_permission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('permission_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'simplewiki', ['Permission'])

        # Adding M2M table for field can_write on 'Permission'
        m2m_table_name = db.shorten_name(u'simplewiki_permission_can_write')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm[u'simplewiki.permission'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['permission_id', 'user_id'])

        # Adding M2M table for field can_read on 'Permission'
        m2m_table_name = db.shorten_name(u'simplewiki_permission_can_read')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm[u'simplewiki.permission'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['permission_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Article', fields ['slug', 'parent']
        db.delete_unique(u'simplewiki_article', ['slug', 'parent_id'])

        # Deleting model 'Article'
        db.delete_table(u'simplewiki_article')

        # Removing M2M table for field related on 'Article'
        db.delete_table(db.shorten_name(u'simplewiki_article_related'))

        # Deleting model 'ArticleAttachment'
        db.delete_table(u'simplewiki_articleattachment')

        # Deleting model 'Revision'
        db.delete_table(u'simplewiki_revision')

        # Deleting model 'Permission'
        db.delete_table(u'simplewiki_permission')

        # Removing M2M table for field can_write on 'Permission'
        db.delete_table(db.shorten_name(u'simplewiki_permission_can_write'))

        # Removing M2M table for field can_read on 'Permission'
        db.delete_table(db.shorten_name(u'simplewiki_permission_can_read'))


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
        u'simplewiki.article': {
            'Meta': {'unique_together': "(('slug', 'parent'),)", 'object_name': 'Article'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': '1', 'blank': 'True'}),
            'current_revision': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'current_rev'", 'unique': 'True', 'null': 'True', 'to': u"orm['simplewiki.Revision']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': '1', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['simplewiki.Article']", 'null': 'True', 'blank': 'True'}),
            'permissions': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['simplewiki.Permission']", 'null': 'True', 'blank': 'True'}),
            'related': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'related_rel_+'", 'null': 'True', 'to': u"orm['simplewiki.Article']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        u'simplewiki.articleattachment': {
            'Meta': {'object_name': 'ArticleAttachment'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['simplewiki.Article']"}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uploaded_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'uploaded_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'simplewiki.permission': {
            'Meta': {'object_name': 'Permission'},
            'can_read': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'read'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'can_write': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'write'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'simplewiki.revision': {
            'Meta': {'object_name': 'Revision'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['simplewiki.Article']"}),
            'contents': ('django.db.models.fields.TextField', [], {}),
            'contents_parsed': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'counter': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'previous_revision': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['simplewiki.Revision']", 'null': 'True', 'blank': 'True'}),
            'revision_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'revision_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'revision_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'wiki_revision_user'", 'null': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['simplewiki']