from caesar.chunks.models import Chunk
from django.contrib.auth.models import User

from django.db import models

class Comment(models.Model):
    TYPE_CHOICES = (
        ('U', 'User'),
        ('S', 'Static analysis'),
        ('T', 'Test result'),
    )
    text = models.TextField()
    chunk = models.ForeignKey(Chunk, related_name='comments')
    author = models.ForeignKey(User)
    start = models.IntegerField() # region start line, inclusive
    end = models.IntegerField() # region end line, exclusive
    type = models.CharField(max_length=1, choices=TYPE_CHOICES, default='U')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', related_name='child_comments', 
        blank=True, null=True)

    def __unicode__(self):
        return self.text

    def vote_counts(self):
        upvote_count = self.votes.filter(value=1).count()
        downvote_count = self.votes.filter(value=-1).count()
        return (upvote_count, downvote_count)

    class Meta:
        ordering = [ 'start', 'end' ]

class Vote(models.Model):
    VALUE_CHOICES = (
        (1, '+1'),
        (-1, '-1'),
    )
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    comment = models.ForeignKey(Comment, related_name='votes')
    author = models.ForeignKey(User)

    class Meta:
        unique_together = ('comment', 'author',)
