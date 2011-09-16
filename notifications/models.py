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


class Event(models.Model):
    CREATED = 'C'
    DELETED = 'D'
    MODIFIED = 'M'
    TYPE_CHOICES = (
            (CREATED, 'Created'),
            (DELETED, 'Deleted'),
            (MODIFIED, 'Modified'),
    )

    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    user = models.ForeignKey(User, blank=True, null=True, related_name='events')
    target_type = models.ForeignKey(ContentType, blank=True, null=True)
    target_id = models.PositiveIntegerField(blank=True, null=True)
    target = generic.GenericForeignKey('target_type', 'target_id')
    created = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=Comment)
def log_comment_save(sender, instance, created=False, **kwargs):
    event_type = Event.CREATED if created else Event.MODIFIED
    event = Event(type=event_type, user=instance.author, target=instance)
    event.save()


@receiver(post_save, sender=Vote)
def log_vote_save(sender, instance, created=False, **kwargs):
    event_type = Event.CREATED if created else Event.MODIFIED
    event = Event(type=event_type, user=instance.author, target=instance)
    event.save()


class Notification(models.Model):
    AUTHORED = 'A'
    ASSIGNED = 'S'
    PARTICIPATED = 'P'
    REASON_CHOICES = (
            (AUTHORED, 'Authored'),
            (ASSIGNED, 'Assigned'),
            (PARTICIPATED, 'Participated'),
    )

    event = models.ForeignKey(Event)
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
    pass
    # if created:
    #     submission_author = instance.chunk.file.submission.author
    #     site = Site.objects.get_current()
    #     context = Context({
    #         'site': site,
    #         'comment': instance,
    #         'chunk': instance.chunk
    #     })
    #     if submission_author and submission_author.email:
    #         to = submission_author.email
    #         subject = NEW_SUBMISSION_COMMENT_SUBJECT_TEMPLATE.render(context)
    #         send_templated_mail(
    #                 subject, None, (to,), 'new_submission_comment', 
    #                 context, template_prefix='notifications/')
    #     if instance.parent and instance.parent.author.email \
    #             and instance.parent.author != instance.author:
    #         to = instance.parent.author.email
    #         subject = NEW_REPLY_SUBJECT_TEMPLATE.render(context)
    #         send_templated_mail(
    #                 subject, None, (to,), 'new_reply', 
    #                 context, template_prefix='notifications/')

