from django.template import Context, Template
from django.template.loader import get_template
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from email_templates import send_templated_mail

from review.models import Comment, Vote
from chunks.models import Submission
import datetime
import sys


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
        ordering = [ '-created' ]


NEW_SUBMISSION_COMMENT_SUBJECT_TEMPLATE = Template(
        "[{{ site.name }}] {{ comment.author.get_full_name|default:comment.author.username }} commented on your code")

NEW_REPLY_SUBJECT_TEMPLATE = Template(
        "[{{ site.name }}] {{ comment.author.get_full_name|default:comment.author.username }} replied to your comment")


@receiver(post_save, sender=Comment)
def send_comment_notification(sender, instance, created=False, **kwargs):
    if created:
        site = Site.objects.get_current()
        context = Context({
            'site': site,
            'comment': instance,
            'chunk': instance.chunk
        })
        #comment gets a reply, the reply is not by the original author
        if instance.parent and instance.parent.author.email \
                and instance.parent.author != instance.author:
            to = instance.parent.author.email
            subject = NEW_REPLY_SUBJECT_TEMPLATE.render(context)
            notification = Notification(recipient = instance.parent.author, reason='R')
            notification.submission = instance.chunk.file.submission
            notification.comment = instance
            notification.save()

            #sent = send_templated_mail(
            #    subject, None, (to,), 'new_reply',
            #    context, template_prefix='notifications/')
            #notification.email_sent = sent
            #notification.save()
            return

        submission_author = instance.chunk.file.submission.author
        submission = instance.chunk.file.submission
        #comment gets made on a submission after code review deadline has passed
        if submission_author and submission_author.email \
                and instance.author != submission_author\
                and instance.author.username != "checkstyle" \
                and datetime.datetime.now() > submission.code_review_end_date():
            to = submission_author.email
            subject = NEW_SUBMISSION_COMMENT_SUBJECT_TEMPLATE.render(context)
            notification = Notification(recipient = submission_author, reason='C')
            notification.submission = instance.chunk.file.submission
            notification.comment = instance
            notification.save()

            #sent = send_templated_mail(
             #       subject, None, (to,), 'new_submission_comment',
              #      context, template_prefix='notifications/')
           # notification.email_sent = sent
            #notification.save()
    pass

