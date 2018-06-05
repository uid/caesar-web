from django.template import Context, Template
from django.template.loader import get_template
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django_tools.middlewares import ThreadLocal

from email_templates import send_templated_mail
import app_settings

import datetime
import sys
import os
import textwrap


class lazy_property(object):
   def __init__(self, func):
       self.func = func

   def __get__(self, instance, cls):
       result = self.func(instance)
       setattr(instance, self.func.__name__, result)
       return result


class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(blank=False, null=False, max_length=32)

    class Meta:
        db_table = u'subjects'

    def __str__(self):
      return self.name

class Semester(models.Model):
    id = models.AutoField(primary_key=True)
    subject = models.ForeignKey(Subject, related_name='semesters')

    description = models.CharField(max_length=140, blank=True, \
        help_text='Subject Name. (ex.) Software Construction')

    semester = models.CharField(blank=True, null=False, max_length=32)
    is_current_semester = models.BooleanField(default=False, verbose_name='Is in progress')

    class Meta:
        db_table = u'semesters'

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
    allow_unextending_to_past = models.BooleanField(default=False, 
        help_text="If enabled, then user can give back extension days even if it pushes their deadline back into the past. "\
                  "If disabled, then user's deadline must always be in the future after a change.")
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)

    class Meta:
        db_table = u'milestones'

    def full_name(self):
        return '%s - %s' % (self.assignment.name, self.name)

    def __unicode__(self):
        return '%s - %s - (%s)' % (self.assignment, self.name, self.get_type_display())

class SubmitMilestone(Milestone):
    class Meta:
        db_table = u'submitmilestones'
    starting_code_path = models.CharField(max_length=300, blank=True, default="", 
                help_text="Folder containing starting code for the assignment.  Should contain one subfolder, usually called staff/, under which is the starting code.")
    submitted_code_path = models.CharField(max_length=300, blank=True, default="",
                help_text="Folder containing student code for the assignment. Should contain subfolders named by student usernames: abc/, def/, ghi/, etc.")
    included_file_patterns = models.CharField(max_length=300, blank=True, default="*.java *.c *.h *.cpp *.CC *.py",
                help_text="Filename patterns to upload, separated by whitespace; e.g. *Foo*.java matches Foo.java and src/TheFool/Bar.java")
    excluded_file_patterns = models.CharField(max_length=300, blank=True, default="",
                help_text="Filename patterns to exclude from upload, separated by whitespace")
    restrict_access = models.BooleanField(default=False,
                help_text="If enabled, restrict who can view the students' chunks to the student authors and any assigned reviewers. "
                          "LAs and TAs will not be able to view submissions if this is enabled.")
    run_checkstyle = models.BooleanField(default=False,
                help_text="If enabled, runs Checkstyle on the students' Java code, and preloads its output as comments in Caesar")
    suppress_checkstyle_regex = models.CharField(max_length=200, blank=True, default="",
                help_text="Regex of checkstyle comments to suppress; separate multiple patterns by |")


@receiver(post_save, sender=SubmitMilestone)
def set_submit_type(sender, instance, created, **kwargs):
    if created:
        instance.type=Milestone.SUBMIT
        instance.save()

class ReviewMilestone(Milestone):
    reviewers_per_chunk = models.IntegerField(default=2)

    # will someday be used by routing
    # student_reviewers_per_chunk = models.IntegerField(default=2)
    # volunteer_reviewers_per_chunk = models.IntegerField(default=2)
    # teacher_reviewers_per_chunk = models.IntegerField(default=1)
    
    min_student_lines = models.IntegerField(default=30)
    submit_milestone = models.ForeignKey(SubmitMilestone, related_name='review_milestone')

    # number of chunks to be assigned to students, alums, and staff in the class
    student_count = models.IntegerField(default=5)
    alum_count = models.IntegerField(default=3)
    staff_count = models.IntegerField(default=10)

    reveal_date = models.DateTimeField(null=True, blank=True, help_text="When comments are revealed to code author. If blank, comments are always visible to author.")

    class Meta:
        db_table = u'reviewmilestones'

@receiver(post_save, sender=ReviewMilestone)
def set_review_type(sender, instance, created, **kwargs):
    if created:
        instance.type=Milestone.REVIEW
        instance.save()

class Batch(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
      db_table = u'batches'
      verbose_name_plural = 'batches'

    def __str__(self):
      return 'batch %s for %s' % (self.id, self.name)


class Submission(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    authors = models.ManyToManyField(User,
            blank=True, related_name='submissions')
    created = models.DateTimeField(auto_now_add=True)
    revision = models.IntegerField(null=True, blank=True)
    revision_date = models.DateTimeField(null=True, blank=True)
    milestone = models.ForeignKey(SubmitMilestone, related_name='submissions')
    batch = models.ForeignKey(Batch, blank=True, null=True, related_name='submissions')
    sha256 = models.CharField(max_length=64, null=True, blank=True) # SHA256 of all files in the submission 

    class Meta:
        db_table = u'submissions'
    def __unicode__(self):
        return '%s, for %s' % (self.name, self.milestone)

    @models.permalink
    def get_absolute_url(self):
        return ('review.views.view_all_chunks', [str(self.milestone.assignment.name), str(self.name), "code"])

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
        try:
            review_milestone = ReviewMilestone.objects.get(submit_milestone=self.milestone)
            return review_milestone.duedate
        except ObjectDoesNotExist:
            return self.milestone.duedate + datetime.timedelta(days=7)
        # this should never happen because submit_milestones should only have one review_milestone
        # although that's not true on our dev server so I'll leave it this way for now
        except MultipleObjectsReturned:
            review_milestones = ReviewMilestone.objects.filter(submit_milestone=self.milestone)
            return review_milestones.latest('duedate').duedate

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

    @lazy_property
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

        # get the authors.
        authors = [str(u.username) for u in self.file.submission.authors.filter()]
        # get the assigned reviewers.
        assigned_reviewers = User.objects.filter(tasks__submission=self.file.submission)
        reviewers = [str(u.username) for u in assigned_reviewers]

        allowed_users = authors + reviewers

        if cinfo.find('restricted') != -1 and not str(usr.username) in allowed_users:
          # Don't stop super users from viewing chunks.
          if not usr.is_superuser:
            raise PermissionDenied
        # logging to make sure the reviewers and authors lists are correct.
        #logger = logging.getLogger(__name__)
        #logger.info("authors" + str(authors) + "\n reviewers:" + str(reviewers));

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
        return ('view_chunk', [str(self.id)])

    def __unicode__(self):
        return u'%s - %s' % (self.name,self.id)

    # # this is never called
    # def sorted_reviewers(self):    
    #     members = self.file.submission.milestone.assignment.semester.members.all()
    #     students = []; alum = []; staff = []
    #     for member in members:
    #         reviewer = member.user.profile
    #         if member.is_student():
    #             students.append(reviewer)
    #         elif member.is_teacher():
    #             staff.append(reviewer)
    #         elif member.is_volunteer():
    #             alum.append(reviewer)
    #     return students + alum + staff

    # dead code, never called
    # def reviewers_comment_strs(self, tasks=None):
    #   #assert False C F check course policy
    #   comment_count = defaultdict(int)
    #   for comment in self.comments.all():
    #     comment_count[comment.author] += 1
    #
    #   if not tasks:
    #     tasks = self.tasks.all()
    #
    #   checkstyle = []; students = []; alum = []; staff = []
    #   for task in tasks:
    #     user_task_dict = {
    #       'username': task.reviewer.username,
    #       'count': comment_count[task.reviewer],
    #       'completed': task.completed,
    #       }
    #
    #     member = task.reviewer.user.memberships.objects.get(user=task.reviewer.user, semester=task.milestone.assignment.semester)
    #     if member.is_student():
    #       students.append(user_task_dict)
    #     elif member.is_teacher():
    #       staff.append(user_task_dict)
    #     elif member.is_volunteer():
    #       alum.append(user_task_dict)
    #     elif task.reviewer.is_checkstyle():
    #       checkstyle.append(user_task_dict)
    #
    #   return [checkstyle, students, alum, staff]

    def reviewer_count(self):
      return self.file.submission.milestone.assignment.semester.members.exclude(user__username = 'checkstyle').count()

    def comment_count(self):
      return self.comments.count()

class StaffMarker(models.Model):
    chunk = models.ForeignKey(Chunk, related_name='staffmarkers')
    start_line = models.IntegerField(blank=True, null=True)
    end_line = models.IntegerField(blank=True, null=True)
    class Meta:
        db_table = u'staffmarkers'


class ChunkReview(models.Model):
    chunk = models.OneToOneField(Chunk, related_name='chunk_review', null=True, blank=True)
    id = models.AutoField(primary_key=True)
    # student_reviewers = models.IntegerField(default=0)
    # alum_reviewers = models.IntegerField(default=0)
    student_or_alum_reviewers = models.IntegerField(default=0)
    staff_reviewers = models.IntegerField(default=0)
    # reviewer_ids = models.TextField(blank=True) #space separated list of chunk names [name checked, ]

    class Meta:
        db_table = 'chunkreviews'

    # def reset(self):
    #     self.student_or_alum_reviewers = 0
    #     self.staff_reviewers = 0

    # def add_reviewer_id(self,id):
    #     self.reviewer_ids += ' ' + str(id)

    # def remove_reviewer_id(self,id):
    #     self.reviewer_ids = self.reviewer_ids.replace(' '+str(id),'')

    # def reviewer_ids(self):
    #     return list(map(int,self.reviewer_ids.split()))

    def __unicode__(self):
        return u'chunk_review - %s' % (self.id)

class Task(models.Model):
    STATUS_CHOICES=(
        ('N', 'New'),
        ('O', 'Opened'),
        ('C', 'Completed'),
        ('U', 'Unfinished'),
    )
    
    submission = models.ForeignKey(Submission, related_name='tasks', null=True, blank=True)
    chunk = models.ForeignKey(Chunk, related_name='tasks', null=True, blank=True)
    chunk_review = models.ForeignKey(ChunkReview, related_name='tasks', null=True, blank=True)
    reviewer = models.ForeignKey(User, related_name='tasks', null=True)
    milestone = models.ForeignKey(ReviewMilestone, related_name='tasks')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='N')
    # TODO switch to a more robust model history tracking (e.g. versioning)
    created = models.DateTimeField(auto_now_add=True)
    opened = models.DateTimeField(blank=True, null=True)
    completed = models.DateTimeField(blank=True, null=True)

    # how should tasks be sorted in the dashboard?
    def sort_key(self):
        try:
            return int(self.submission.name)
        except:
            return self.submission.name

    class Meta:
        db_table = 'tasks'
        unique_together = ('chunk', 'reviewer',)

    def __unicode__(self):
        return "Task: %s - %s" % (self.reviewer, self.chunk)

    def mark_as(self, status):
        if status not in zip(*Task.STATUS_CHOICES)[0]:
            raise Exception('Invalid task status')

        self.status = status
        if status == 'N':
            self.opened = None
            self.completed = None
        elif status == 'O':
            self.opened = datetime.datetime.now()
        elif status == 'C':
            self.completed = datetime.datetime.now()

        self.save()

    def name(self):
        return self.chunk.name if self.chunk != None else self.submission.name
    
    def authors(self):
      return self.submission.authors


class Comment(models.Model):
    TYPE_CHOICES = (
        ('U', 'User'),
        ('S', 'Static analysis'),
        ('T', 'Test result'),
    )
    text = models.TextField()
    chunk = models.ForeignKey(Chunk, related_name='comments')
    author = models.ForeignKey(User, related_name='comments')
    start = models.IntegerField() # region start line, inclusive
    end = models.IntegerField() # region end line, exclusive
    type = models.CharField(max_length=1, choices=TYPE_CHOICES, default='U')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    edited = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey('self', related_name='child_comments',
        blank=True, null=True)
    # fields added for denormalization purposes
    upvote_count = models.IntegerField(default=0)
    downvote_count = models.IntegerField(default=0)
    # Set to either self.id for root comments or parent.id for replies, mostly
    # to allow for retrieving comments in threaded order in one query
    thread_id = models.IntegerField(null=True)
    deleted = models.BooleanField(default=False)
    batch = models.ForeignKey(Batch, blank=True, null=True, related_name='comments')
    similar_comment = models.ForeignKey('self', related_name='similar_comments', blank=True, null=True)

    class Meta:
        db_table = 'comments'
        ordering = [ 'start', '-end', 'thread_id', 'created' ]

    def __unicode__(self):
        return self.text

    def save(self, *args, **kwargs):
        super(Comment, self).save(*args, **kwargs)
        self.thread_id = self.parent_id or self.id
        super(Comment, self).save(*args, **kwargs)

    #returns child and vote counts for child as a tuple
    def get_child_comment_vote(self):
        return map(self.get_comment_vote, self.child_comments)

    def is_edited(self):
        if self.edited is not None and self.edited > self.created:
            return True
        return False

    def get_comment_vote(self):
        try:
            vote = self.votes.get(author=request.user.id).value
        except Vote.DoesNotExist:
            vote = None
        return (self, vote)

    def is_reply(self):
        return self.parent_id is not None

    def generate_snippet(self):
        snippet_length = 90
        if len(self.text) < snippet_length:
            return self.text
        return self.text[0:snippet_length] + "..."

    def is_checkstyle(self):
      return self.author.username is 'checkstyle'


class Vote(models.Model):
    VALUE_CHOICES = (
        (1, '+1'),
        (-1, '-1'),
    )
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    comment = models.ForeignKey(Comment, related_name='votes')
    author = models.ForeignKey(User, related_name='votes')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    REPUTATION_WEIGHT = 1

    class Meta:
        db_table = 'votes'
        unique_together = ('comment', 'author',)

    def __unicode__(self):
        return u'Vote(value=%s, comment=%s)' % (self.value, self.comment)



@receiver(pre_save, sender=Vote)
def update_reputation_on_vote_save(sender, instance, raw=False, **kwargs):
    if not raw:
        comment_author = instance.comment.author
        if instance.id:
            old_vote = Vote.objects.get(pk=instance.id)
            if old_vote.value > 0:
                comment_author.profile.reputation -= old_vote.value * Vote.REPUTATION_WEIGHT

        new_value = int(instance.value)
        if new_value > 0:
            comment_author.profile.reputation += new_value * Vote.REPUTATION_WEIGHT

        comment_author.profile.save()


@receiver(pre_delete, sender=Vote)
def update_reputation_on_vote_delete(sender, instance, **kwargs):
    if instance.value > 0:
        comment_author = instance.comment.author
        comment_author.profile.reputation -= instance.value * Vote.REPUTATION_WEIGHT
        comment_author.profile.save()


@receiver(post_save, sender=Vote)
@receiver(post_delete, sender=Vote)
def denormalize_votes(sender, instance, created=False, **kwargs):
    """This recalculates the vote totals for the comment being voted on"""
    try:
        comment = instance.comment
        comment.upvote_count = comment.votes.filter(value=1).count()
        comment.downvote_count = comment.votes.filter(value=-1).count()
        comment.save()
    except Comment.DoesNotExist:
        # vote is getting deleted from a comment delete cascade, do nothing
        pass
    except Chunk.DoesNotExist:
        # vote is getting deleted from a comment delete cascade, do nothing
        pass


class Notification(models.Model):
    SUMMARY = 'S'
    RECEIVED_REPLY = 'R'
    COMMENT_ON_SUBMISSION = 'C'
    REASON_CHOICES = (
            (SUMMARY, 'Summary'),
            (RECEIVED_REPLY, 'Received reply'),
            (COMMENT_ON_SUBMISSION, 'Received comment on submission'),
    )

    submission = models.ForeignKey(Submission, blank=True, null=True, related_name='notifications')
    comment = models.ForeignKey(Comment, blank=True, null=True, related_name='notifications')
    recipient = models.ForeignKey(User, related_name='notifications')
    reason = models.CharField(max_length=1, blank=True, choices=REASON_CHOICES)
    created = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'notifications'
        ordering = [ '-created' ]


# NEW_SUBMISSION_COMMENT_SUBJECT_TEMPLATE = Template(
#         "[Caesar] {{ comment.author.get_full_name|default:comment.author.username }} commented on your code")

# NEW_REPLY_SUBJECT_TEMPLATE = Template(
#         "[Caesar] {{ comment.author.get_full_name|default:comment.author.username }} replied to your comment")

# uncomment this when we're ready to send email notifications again
# @receiver(post_save, sender=Comment)
# def send_comment_notification(sender, instance, created=False, raw=False, **kwargs):
#     if created and not raw:
#         context = Context({
#             'comment': instance,
#             'chunk': instance.chunk
#         })
#         #comment gets a reply, the reply is not by the original author
#         if instance.parent and instance.parent.author.email \
#                 and instance.parent.author != instance.author:
#             to = instance.parent.author.email
#             subject = NEW_REPLY_SUBJECT_TEMPLATE.render(context)
#             notification = Notification(recipient = instance.parent.author, reason='R')
#             notification.submission = instance.chunk.file.submission
#             notification.comment = instance
#             notification.save()

#             #sent = send_templated_mail(
#             #    subject, None, (to,), 'new_reply',
#             #    context, template_prefix='')
#             #notification.email_sent = sent
#             #notification.save()
#             return

#         return # NOTE(TFK): The code below is broken since submissions can have multiple authors.
#         submission_author = instance.chunk.file.submission.author
#         submission = instance.chunk.file.submission
#         #comment gets made on a submission after code review deadline has passed
#         if submission_author and submission_author.email \
#                 and instance.author != submission_author\
#                 and instance.author.username != "checkstyle" \
#                 and datetime.datetime.now() > submission.code_review_end_date():
#             to = submission_author.email
#             subject = NEW_SUBMISSION_COMMENT_SUBJECT_TEMPLATE.render(context)
#             notification = Notification(recipient = submission_author, reason='C')
#             notification.submission = instance.chunk.file.submission
#             notification.comment = instance
#             notification.save()

#             #sent = send_templated_mail(
#              #       subject, None, (to,), 'new_submission_comment',
#               #      context, template_prefix='')
#            # notification.email_sent = sent
#             #notification.save()
#     pass


class Extension(models.Model):
    user = models.ForeignKey(User, related_name='extensions')
    milestone = models.ForeignKey(Milestone, related_name='extensions')
    slack_used = models.IntegerField(default=0, blank=True, null=True)

    class Meta:
        db_table = 'extensions'
        unique_together = ('user', 'milestone',)

    def assignment(self):
        return self.milestone.assignment

    def new_duedate(self):
        return self.milestone.duedate + datetime.timedelta(days=self.slack_used)

    def __str__(self):
      return '%s (%s) %s days' % (self.user.username, self.milestone.full_name(), self.slack_used)

class Member(models.Model):
    STUDENT = 'S'
    TEACHER = 'T'
    VOLUNTEER = 'V'
    ROLE_CHOICES = (
        (STUDENT, 'student'),
        (TEACHER, 'teacher'),
        (VOLUNTEER, 'volunteer'),
    )

    role = models.CharField(max_length=1, choices=ROLE_CHOICES)
    slack_budget = models.IntegerField(default=5, blank=False, null=False)
    user = models.ForeignKey(User, related_name='membership')
    semester = models.ForeignKey(Semester, related_name='members')

    class Meta:
        db_table = 'members'

    def __str__(self):
      return '%s (%s), %s' % (self.user.username, self.get_role_display(), self.semester)

    def is_student(self):
        return self.role == Member.STUDENT

    def is_teacher(self):
        return self.role == Member.TEACHER

    def is_volunteer(self):
        return self.role == Member.VOLUNTEER

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    reputation = models.IntegerField(default=0, editable=True)

    class Meta:
        db_table = 'userprofiles'

    def __unicode__(self):
        return self.user.__unicode__()

    def name(self):
      if self.user.first_name and self.user.last_name:
        return self.user.first_name + ' ' + self.user.last_name
      return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        profile, created = UserProfile.objects.get_or_create(user=instance)
        if created:
            profile.save()


