import app_settings
import datetime
import logging
import textwrap
import tasks

from accounts.fields import MarkdownTextField
from collections import defaultdict
from django_tools.middlewares import ThreadLocal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.dispatch import receiver
from pygments.formatters import HtmlFormatter


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

    class Meta:
        db_table = u'assignments'

    def __unicode__(self):
        return '%s, %s' % (self.name, self.semester)

    def is_current_semester(self):
        return self.semester.is_current_semester

    def is_live_assignment(self):
        return self.milestones.latest('assigned_date').assigned_date and datetime.datetime.now() < self.milestones.latest('duedate').duedate

class Milestone(models.Model):
    SUBMIT = 'S'
    REVIEW = 'R'
    TYPE_CHOICES = (
        (SUBMIT, 'Submit'),
        (REVIEW, 'Review'),
    )

    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(Assignment, related_name='milestones')
    assigned_date = models.DateTimeField(null=True, blank=True)
    duedate = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=50)
    max_extension = models.IntegerField(default=2)
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)

    def full_name(self):
        return '%s - %s' % (self.assignment.name, self.name)

    def __unicode__(self):
        return '%s - %s - (%s)' % (self.assignment, self.name, self.get_type_display())

class SubmitMilestone(Milestone):
    pass

@receiver(post_save, sender=SubmitMilestone)
def set_submit_type(sender, instance, created, **kwargs):
    if created:
        instance.type=Milestone.SUBMIT
        instance.save()

class ReviewMilestone(Milestone):
    reviewers_per_chunk = models.IntegerField(default=2)
    min_student_lines = models.IntegerField(default=30)
    submit_milestone = models.ForeignKey(SubmitMilestone, related_name='review_milestones')
    chunks_to_assign = models.TextField(blank = True, null=True) #space separated list of chunk names [name checked, ]

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

    def num_tasks_for_user(self, user):
      if user.role == 'student':
        return self.student_count
      elif user.role == 'staff':
        return self.staff_count
      else:
        return self.alum_count

@receiver(post_save, sender=ReviewMilestone)
def create_current_review_milestone(sender, instance, created, **kwargs):
    if created:
        # This code appears to copy parms from previous assignments in that semester.
        past = ReviewMilestone.objects.filter(assignment__semester = instance.assignment.semester).order_by('-duedate').exclude(id = instance.id)
        if past.count() > 0:
            pick = past[0]
            for milestone in past:
                #check that the assignment had tasks assigned
                chunks = Chunk.objects.filter(tasks__milestone=milestone)
                tasks = False
                for chunk in chunks:
                    if chunk.tasks.count() > 0:
                        pick = milestone
                        tasks = True
                        break
                if tasks:
                    break
            #set number of tasks
            instance.student_count_default = pick.student_count
            instance.alum_count_default = pick.alum_count
            instance.staff_count_default = pick.staff_count
            #set number of students we can expect
            users = User.objects.filter(profile__tasks__milestone= pick).distinct()
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

@receiver(post_save, sender=ReviewMilestone)
def set_review_type(sender, instance, created, **kwargs):
    if created:
        instance.type=Milestone.REVIEW
        instance.save()

class Batch(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
      verbose_name_plural = 'batches'

    def __str__(self):
      return 'batch %s for %s' % (self.id, self.name)


class Submission(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    authors = models.ManyToManyField(User,
            blank=True, null=True, related_name='submissions')
    created = models.DateTimeField(auto_now_add=True)
    revision = models.IntegerField(null=True, blank=True)
    revision_date = models.DateTimeField(null=True, blank=True)
    milestone = models.ForeignKey(SubmitMilestone, related_name='submissions')
    batch = models.ForeignKey(Batch, blank=True, null=True, related_name='submissions')
    published = models.BooleanField()

    class Meta:
        db_table = u'submissions'
    def __unicode__(self):
        return '%s, for %s' % (self.name, self.milestone)

    @models.permalink
    def get_absolute_url(self):
        return ('chunks.views.view_all_chunks', [str(self.milestone.assignment.name), str(self.name), "code"])

    def has_author(self, user):
        return self.authors.filter(pk=user.pk).exists()

    def assignment(self):
        return self.milestone.assignment

    def chunk_count(self):
        return len(self.chunks())

    def chunks(self):
        chunks = []
        for f in self.files.filter():
            chunks.extend(f.chunks.filter())
        return chunks

    def code_review_end_date(self):
        review_milestones = ReviewMilestone.objects.filter(submit_milestone=self.milestone)
        if review_milestones:
            return review_milestones.latest('duedate').duedate
        else:
            return self.milestone.duedate + datetime.timedelta(days=7)

class File(models.Model):
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=200)
    data = models.TextField()
    submission = models.ForeignKey(Submission, related_name='files')
    created = models.DateTimeField(auto_now_add=True)
    def __split_lines(self):
        # first_line_offset = 0
        # offset = 0
        # while self.data[first_line_offset] == '\n' or self.data[first_line_offset] == '\r':
        #     if self.data[first_line_offset] == '\n':
        #         offset += 1
        #     first_line_offset += 1
        # offset +=1

        self.lines = list(enumerate(self.data.splitlines(), start = 1))

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
        return self.filter(file__submission__milestone__assignment=assignment)

import pdb

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
        self._check_permissions()
        if not hasattr(self, '_lines'):
            self._split_lines()

        return self._lines

    def _check_permissions(self):
        usr = ThreadLocal.get_current_user()

        # The chunk_info field is set to 'restricted' if only authors and
        # reviewers of the chunk are allowed to view it.
        if self.chunk_info == None:
          cinfo = ""
        else:
          cinfo = self.chunk_info

        return

        # get the authors.
        authors = [str(u.username) for u in self.file.submission.authors.filter()]
        # get the assigned reviewers.
        assigned_reviewers = User.objects.filter(profile__tasks__submission=self.file.submission)
        reviewers = [str(u.username) for u in assigned_reviewers]

        allowed_users = authors + reviewers

        if cinfo.find('restricted') != -1 and not str(usr.username) in allowed_users:
          # Don't stop super users from viewing chunks.
          if not usr.is_superuser:
            raise PermissionDenied
        # logging to make sure the reviewers and authors lists are correct.
        logger = logging.getLogger(__name__)
        logger.info("authors" + str(authors) + "\n reviewers:" + str(reviewers));

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
        #data = str(usr.__unicode__())
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
        #NOTE(TFK): Consider uncommenting this so that 6.172 shows
        # a snippet that's actually useful to the mentors.
        #if self.chunk_info == None:
        #  cinfo = ""
        #else:
        #  cinfo = self.chunk_info
        #if cinfo.find('restricted') != -1:
        #  markers = self.staffmarkers.all()
        #  total_lines = 0
        #  for marker in markers:
        #    total_lines += marker.end_line - marker.start_line
        #  student_lines = len(self.file.lines) - total_lines
        #  return "Student Lines: " + str(student_lines) + ", Staff Lines: "+str(total_lines)

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
      #assert False C F check course policy
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
