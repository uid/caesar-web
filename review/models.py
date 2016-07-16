from django.template import Context, Template
from django.template.loader import get_template
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.db.models.signals import pre_save, post_save,\
        pre_delete, post_delete
from django.dispatch import receiver
from django.conf import settings

from accounts.models import UserProfile
from chunks.models import Submission, Chunk, Batch

from email_templates import send_templated_mail

import datetime
import sys

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

    class Meta:
        ordering = [ 'start', '-end', 'thread_id', 'created' ]

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

    def __unicode__(self):
        return u'Vote(value=%s, comment=%s)' % (self.value, self.comment)

    class Meta:
        unique_together = ('comment', 'author',)


@receiver(pre_save, sender=Vote)
def update_reputation_on_vote_save(sender, instance, raw=False, **kwargs):
    if not raw:
        comment_author = instance.comment.author.get_profile()
        if instance.id:
            old_vote = Vote.objects.get(pk=instance.id)
            if old_vote.value > 0:
                comment_author.reputation -= old_vote.value * Vote.REPUTATION_WEIGHT

        new_value = int(instance.value)
        if new_value > 0:
            comment_author.reputation += new_value * Vote.REPUTATION_WEIGHT

        comment_author.save()


@receiver(pre_delete, sender=Vote)
def update_reputation_on_vote_delete(sender, instance, **kwargs):
    if instance.value > 0:
        comment_author = instance.comment.author.get_profile()
        comment_author.reputation -= instance.value * Vote.REPUTATION_WEIGHT
        comment_author.save()


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


class Star(models.Model):
    value = models.BooleanField(default=False)
    chunk = models.ForeignKey(Chunk, related_name="stars")
    author = models.ForeignKey(User, related_name="stars")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)




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
        db_table = 'notifications_notification'
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
#             #    context, template_prefix='review/')
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
#               #      context, template_prefix='review/')
#            # notification.email_sent = sent
#             #notification.save()
#     pass

