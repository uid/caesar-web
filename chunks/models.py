import textwrap

from pygments import highlight
from pygments.lexers import JavaLexer
from pygments.formatters import HtmlFormatter

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

import app_settings

class Assignment(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = u'assignments'
    def __unicode__(self):
        return self.name


class Submission(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    assignment = models.ForeignKey(Assignment, related_name='submissions')
    author = models.ForeignKey(User, 
            blank=True, null=True, related_name='submissions')
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = u'submissions'
    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        return ('chunks.views.view_all_chunks', [str(self.assignment.name), str(self.name), "code"])
 

class File(models.Model):
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=200)
    data = models.TextField()
    submission = models.ForeignKey(Submission, related_name='files')
    created = models.DateTimeField(auto_now_add=True)
    def __split_lines(self):
        # move forward
        first_line_offset = 0
        offset = 0
        while self.data[first_line_offset] == '\n' or self.data[first_line_offset] == '\r':
            if self.data[first_line_offset] == '\n':
                offset += 1
            first_line_offset += 1
        offset +=1
        self.lines = list(enumerate(self.data.splitlines(), start = offset))
        
    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)
        self.__split_lines()
    class Meta:
        db_table = u'files'
        unique_together = (('path', 'submission'))
    def __unicode__(self):
        return self.path


class ChunkManager(models.Manager):
    def find_by_assignment(self, assignment):
        return self.filter(file__submission__assignment=assignment)


class Chunk(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.ForeignKey(File, related_name='chunks')
    name = models.CharField(max_length=200)
    start = models.IntegerField()
    end = models.IntegerField()
    cluster_id = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    objects = ChunkManager()
    class Meta:
        db_table = u'chunks'

    @property
    def data(self):
        if not hasattr(self, '_data'): 
            self._split_lines()
        return self._data

    @property
    def lines(self):
        if not hasattr(self, '_lines'): 
            self._split_lines()
        return self._lines
    
    def _split_lines(self):
        file_data = self.file.data
        # Rewind backwards from the offset to the beginning of the line
        first_line_offset = self.start
        while file_data[first_line_offset] != '\n':
            first_line_offset -= 1
        first_line_offset += 1
        first_line = file_data.count("\n", 0, first_line_offset) + 1

        # TODO: make tab expansion configurable
        # TODO: more robust (custom) dedenting code
        data = file_data[first_line_offset:self.end].expandtabs(4)
        self._data = textwrap.dedent(data)
        self._lines = list(enumerate(self.data.splitlines(), start=first_line))

    def save(self, *args, **kwargs):
        super(Chunk, self).save(*args, **kwargs)
        self._split_lines()

    # def get_comment_vote_snippet(self, comment):
    #   vote = user_votes.get(comment.id, None)
    #   snippet = self.generate_snippet(comment.start, comment.end)
    #   return (comment, vote, snippet)
    # 
    # def get_comment_data(self):
    #   return map(self.get_comment_vote_snippet,
    #           Comment.get_comments_for_chunk(self))
        
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
    
    def get_highlighted_lines(self):
        lexer = JavaLexer()
        formatter = HtmlFormatter(cssclass='syntax', nowrap=True)
        numbers, lines = zip(*self.lines)
        # highlight the code this way to correctly identify multi-line
        # constructs
        # TODO implement a custom formatter to do this instead
        highlighted_lines = zip(numbers, 
                highlight(self.data, lexer, formatter).splitlines())
        return highlighted_lines

    def get_similar_chunks(self):
        if not self.cluster_id:
            return []
        limit = app_settings.SIMILAR_CHUNK_LIMIT
        chunks = Chunk.objects.filter(cluster_id=self.cluster_id) \
                .exclude(id=self.id)[:limit]
        return chunks

    @models.permalink
    def get_absolute_url(self):
        return ('chunks.views.view_chunk', [str(self.id)])

    def __unicode__(self):
        return u'%s' % (self.name,)


class Fingerprint(models.Model):
    # This ID is basically useless, but Django currently doesn't support
    # composite primary keys
    id = models.AutoField(primary_key=True)
    chunk = models.ForeignKey(Chunk, related_name='fingerprints', 
                              db_index=True, editable=False)
    value = models.IntegerField(db_index=True, editable=False)
    position = models.IntegerField(editable=False)

    class Meta:
        unique_together = ('chunk', 'position',)
        db_table = u'fingerprints'

    def __unicode__(self):
        return u'%d: [%d, %d]' % (self.chunk_id, self.position, self.value)
