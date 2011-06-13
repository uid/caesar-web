from django.db import models
from django.conf import settings

import textwrap

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
    name = models.CharField(max_length=200)
    start = models.IntegerField()
    end = models.IntegerField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    class Meta:
        db_table = u'chunks'
    
    def __split_lines(self):
        file_data = self.file.data
        # Rewind backwards from the offset to the beginning of the line
        first_line_offset = self.start
        while file_data[first_line_offset] != '\n':
            first_line_offset -= 1
        first_line_offset += 1
        first_line = file_data.count("\n", 0, first_line_offset)+1

        # TODO: make tab expansion configurable
        # TODO: more robust (custom) dedenting code
        data = file_data[first_line_offset:self.end].expandtabs(4)
        self.lines = list(enumerate(textwrap.dedent(data).splitlines(), 
            start=first_line))

    def __init__(self, *args, **kwargs):
        super(Chunk, self).__init__(*args, **kwargs)
        self.__split_lines()

    def save(self, *args, **kwargs):
        super(Chunk, self).save(*args, **kwargs)
        self.__split_lines()

    def generate_snippet(self, start=None, end=None):
        if start is None:
            start = self.lines[0][0]
        if end is None:
            end = self.lines[-1][0]

        line_offset = self.lines[0][0]
        snippet_length = 0
        start_line = start - line_offset
        end_line = start - line_offset
        last_line = len(self.lines) - 1
        
        # first, search forward and gather text
        while snippet_length < settings.MINIMUM_SNIPPET_LENGTH and \
                end_line < last_line:
            snippet_length += len(self.lines[end_line][1].strip()) + 1
            end_line += 1
        # if necessary, scan backwards
        # while snippet_length < settings.MINIMUM_SNIPPET_LENGTH and \
        #         start_line >= 0:
        #     snippet_length += len(self.lines[start_line][1].strip()) + 1
        #     start_line -= 1
        snippet_lines = self.lines[start_line:end_line + 1]
        return ' '.join(zip(*snippet_lines)[1])


    @models.permalink
    def get_absolute_url(self):
        return ('chunks.views.view_chunk', [str(self.id)])

    def __unicode__(self):
        return u'%s' % (self.id,)

