import textwrap

import tasks

from pygments import highlight
from pygments.lexers import JavaLexer
from pygments.formatters import HtmlFormatter

from accounts.fields import MarkdownTextField

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver

import datetime
import app_settings
from collections import defaultdict

class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(blank=False, null=False, max_length=32)

    def __str__(self):
      return self.name

class Semester(models.Model):
    id = models.AutoField(primary_key=True)
    subject = models.ForeignKey(Subject, related_name='semesters')

    description = models.CharField(max_length=140, blank=True, \
        help_text='Subject Name. (ex.) Software Construction')
    about = MarkdownTextField(allow_html=False, blank=True, \
        help_text='Format using <a href="http://stackoverflow.com/editing-help">Markdown</a>.')

    semester = models.CharField(blank=True, null=False, max_length=32)
    is_current_semester = models.BooleanField(default=False, verbose_name='Is in progress')

    def __str__(self):
      return '%s - %s' % (self.subject, self.semester)

class Assignment(models.Model):
    id = models.AutoField(primary_key=True)
    semester = models.ForeignKey(Semester, related_name='assignments', blank=False, null=True)
    name = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    duedate = models.DateTimeField(null=True, blank=True)
    code_review_end_date = models.DateTimeField(null=True, blank=True)
    is_live = models.BooleanField(default=False)
    max_extension = models.IntegerField(default=2)
    multiplier = models.IntegerField(default=1)
    student_count = models.IntegerField(default=5)
    student_count_default = models.IntegerField(default=5)
    alum_count = models.IntegerField(default=3)
    alum_count_default = models.IntegerField(default=3)
    staff_count = models.IntegerField(default=10)
    staff_count_default = models.IntegerField(default=10)

    students = models.IntegerField(default=199)
    students_default = models.IntegerField(default=199)
    alums = models.IntegerField(default=1)
    alums_default = models.IntegerField(default=1)
    staff = models.IntegerField(default=15)
    staff_default = models.IntegerField(default=15)

    reviewers_per_chunk = models.IntegerField(default=2)
    min_student_lines = models.IntegerField(default=30)

    chunks_to_assign = models.TextField(blank = True, null=True) #space separated list of chunk names [name checked, ]

    class Meta:
        db_table = u'assignments'
    def __unicode__(self):
        return '%s, %s' % (self.name, self.semester)
    def is_current_semester(self):
        return self.semester.is_current_semester
    def is_life_assignment(self):
        return datetime.datetime.now() < submission.assignment.code_review_end_date and self.is_live

    def num_tasks_for_user(self, user):
      if user.role == 'student':
        return self.student_count
      elif user.role == 'staff':
        return self.staff_count
      else:
        return self.alum_count

@receiver(post_save, sender=Assignment)
def create_current_assignment(sender, instance, created, **kwargs):
    if created:
        # This code appears to copy parms from previous assignments in that semester.
        past = Assignment.objects.filter(semester = instance.semester).order_by('duedate').exclude(id = instance.id).reverse()
        if past.count() > 0:
            pick = past[0]
            for assignment in past:
                #check that the assignment had tasks assigned
                chunks = Chunk.objects.filter(file__submission__assignment=assignment)
                tasks = False
                for chunk in chunks:
                    if chunk.tasks.count() > 0:
                        pick = assignment
                        tasks = True
                        break
                if tasks:
                    break
            #set number of tasks
            instance.student_count_default = pick.student_count
            instance.alum_count_default = pick.alum_count
            instance.staff_count_default = pick.staff_count
            #set number of students we can expect
            users = User.objects.filter(profile__tasks__chunk__file__submission__assignment = pick).distinct()
            students = users.filter(profile__role='S')
            alums = users.exclude(profile__role='S').exclude(profile__role='T')
            staff = users.filter(profile__role='T')
            instance.students_default = students.count()
            instance.alums_default = alums.count()
            instance.staff_default = staff.count()
        else:
            instance.students_default = User.objects.filter(profile__role = 'S').count()
            instance.staff_default = User.objects.filter(profile__role = 'T').count()
        instance.students = instance.students_default
        instance.alums = instance.alums_default
        instance.staff = instance.staff_default
        instance.student_count = instance.student_count_default
        instance.alum_count = instance.alum_count_default
        instance.staff_count = instance.staff_count_default
        instance.save()


class Batch(models.Model):
    assignment = models.ForeignKey(Assignment, related_name='batches')
    is_live = models.BooleanField(default=False)

    class Meta:
      verbose_name_plural = 'batches'

    def __str__(self):
      return 'batch %s for %s' % (self.id, self.assignment)


class Submission(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    assignment = models.ForeignKey(Assignment, related_name='submissions')
    author = models.ForeignKey(User,
            blank=True, null=True, related_name='submissions')
    created = models.DateTimeField(auto_now_add=True)
    revision = models.IntegerField(null=True, blank=True)
    revision_date = models.DateTimeField(null=True, blank=True)
    duedate = models.DateTimeField(null=True, blank=True)
    batch = models.ForeignKey(Batch, blank=True, null=True, related_name='submissions')

    class Meta:
        db_table = u'submissions'
    def __unicode__(self):
        return '%s, for %s' % (self.name, self.assignment)

    @models.permalink
    def get_absolute_url(self):
        return ('chunks.views.view_all_chunks', [str(self.assignment.name), str(self.name), "code"])

    def chunk_count(self):
        return len(self.chunks())

    def chunks(self):
        chunks = []
        for f in self.files.filter():
            chunks.extend(f.chunks.filter())
        return chunks

@receiver(post_save, sender=Assignment)
def create_user_submission(sender, instance, created, **kwargs):
    if created:
        users = User.objects.filter(profile__role='S')
        for auser in users:
            submission, created = Submission.objects.get_or_create(assignment=instance, name=auser.username,
                                                                   author=auser, duedate=instance.duedate)

class File(models.Model):
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=200)
    data = models.TextField()
    submission = models.ForeignKey(Submission, related_name='files')
    batch = models.ForeignKey(Batch, blank=True, null=True, related_name='files')
    created = models.DateTimeField(auto_now_add=True)
    def __split_lines(self):
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
        return '%s - %s' % (self.path, self.submission)


class ChunkManager(models.Manager):
    def find_by_assignment(self, assignment):
        return self.filter(file__submission__assignment=assignment)


class Chunk(models.Model):
    CLASS_TYPE_CHOICES = (
        ('ENUM', 'enum'),
        ('EXCE', 'exception'),
        ('TEST', 'test'),
        ('NONE', 'none'),
    )
    id = models.AutoField(primary_key=True)
    file = models.ForeignKey(File, related_name='chunks')
    name = models.CharField(max_length=200)
    start = models.IntegerField()
    end = models.IntegerField()
    cluster_id = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    class_type = models.CharField(max_length=4, choices=CLASS_TYPE_CHOICES,
                            blank=True, null=True)
    staff_portion = models.IntegerField(default=0)
    student_lines = models.IntegerField(default=0)
    chunk_info = models.TextField(blank=True, null=True)

    simulated_tasks = None

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
        while first_line_offset >= -len(file_data) and file_data[first_line_offset] != '\n':
            first_line_offset -= 1
        first_line_offset += 1
        if first_line_offset < 0:
            first_line_offset=0
        first_line = file_data.count("\n", 0, first_line_offset) + 1

        # TODO: make tab expansion configurable
        # TODO: more robust (custom) dedenting code
        data = file_data[first_line_offset:self.end].expandtabs(4)
        self._data = textwrap.dedent(data)
        self._lines = list(enumerate(self.data.splitlines(), start=first_line))

    def staff_percentage(self):
        markers = self.staffmarkers.all()
        total_lines = 0
        for marker in markers:
            total_lines += marker.end_line - marker.start_line
        return float(total_lines)/len(self.file.lines)

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
        self.start_line = max(0, start_line)
        self.end_line = end_line+1
        snippet_lines = self.lines[self.start_line:self.end_line + 1]
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

    def sorted_reviewers(self):
        students = []; alum = []; staff = []
        for reviewer in self.reviewers.filter():
            if reviewer.is_student():
                students.append(reviewer)
            elif reviewer.is_staff():
                staff.append(reviewer)
            else:
                alum.append(reviewer)
        return students + alum + staff

    def reviewers_comment_strs(self, tasks=None):
      comment_count = defaultdict(int)
      for comment in self.comments.all():
        comment_count[comment.author.profile] += 1

      if not tasks:
        tasks = self.tasks.all()

      checkstyle = []; students = []; alum = []; staff = []
      for task in tasks:
        user_task_dict = {
          'username': task.reviewer.user.username,
          'count': comment_count[task.reviewer],
          'completed': task.completed,
          }

        if task.reviewer.is_student():
          students.append(user_task_dict)
        elif task.reviewer.is_staff():
          staff.append(user_task_dict)
        elif task.reviewer.is_checkstyle():
          checkstyle.append(user_task_dict)
        else:
          alum.append(user_task_dict)

      return [checkstyle, students, alum, staff]

    def reviewer_count(self):
      return len(self.sorted_reviewers())

    def comment_count(self):
      return len(self.comments.filter())

class StaffMarker(models.Model):
    chunk = models.ForeignKey(Chunk, related_name='staffmarkers')
    start_line = models.IntegerField(blank=True, null=True)
    end_line = models.IntegerField(blank=True, null=True)
