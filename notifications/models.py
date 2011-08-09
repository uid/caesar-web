from django.template import Context, Template
from django.template.loader import get_template
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site

from email_templates import send_templated_mail

from review.models import Comment


NEW_SUBMISSION_COMMENT_SUBJECT_TEMPLATE = Template(
        "[{{ site.name }}] {{ comment.author.get_full_name|default:comment.author.username }} commented on your code")

NEW_REPLY_SUBJECT_TEMPLATE = Template(
        "[{{ site.name }}] {{ comment.author.get_full_name|default:comment.author.username }} replied to your comment")


@receiver(post_save, sender=Comment)
def send_comment_notification(sender, instance, created=False, **kwargs):
    if created:
        submission_author = instance.chunk.file.submission.author
        site = Site.objects.get_current()
        context = Context({
            'site': site,
            'comment': instance,
            'chunk': instance.chunk
        })
        if submission_author.email:
            to = submission_author.email
            subject = NEW_SUBMISSION_COMMENT_SUBJECT_TEMPLATE.render(context)
            send_templated_mail(
                    subject, None, (to,), 'new_submission_comment', 
                    context, template_prefix='notifications/')
        if instance.parent and instance.parent.author.email \
                and instance.parent.author != instance.author:
            to = instance.parent.author.email
            subject = NEW_REPLY_SUBJECT_TEMPLATE.render(context)
            send_templated_mail(
                    subject, None, (to,), 'new_reply', 
                    context, template_prefix='notifications/')

