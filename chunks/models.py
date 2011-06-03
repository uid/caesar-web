from django.db import models

class Assignment(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    created = models.DateTimeField()
    class Meta:
        db_table = u'assignments'

class Submission(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    assignment = models.ForeignKey(Assignment)
    created = models.DateTimeField()
    class Meta:
        db_table = u'submissions'

class File(models.Model):
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=200)
    data = models.TextField()
    submission = models.ForeignKey(Submission)
    created = models.DateTimeField()
    class Meta:
        db_table = u'files'
        unique_together = (('path', 'submission'))

class Chunk(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.ForeignKey(File)
    start = models.IntegerField()
    end = models.IntegerField()
    created = models.DateTimeField()
    class Meta:
        db_table = u'chunks'

    @models.permalink
    def get_absolute_url(self):
        return ('caesar.chunks.views.view_chunk', [str(self.id)])

    def __unicode__(self):
        return u'%s' % (self.id,)


