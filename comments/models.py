from chunks.models import Chunk
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
		"""Returns the total upvote and downvote counts as a tuple."""
		upvote_count = self.votes.filter(value=1).count()
		downvote_count = self.votes.filter(value=-1).count()
		return (upvote_count, downvote_count)

	#returns child and vote counts for child as a tuple
	def get_child_comment_vote(self):
		return map(self.get_comment_vote, self.child_comments)

	def get_comment_vote(self):
		try:
			vote = self.votes.get(author=request.user.id).value
		except Vote.DoesNotExist:
			vote = None
		return (self, vote)

	def is_reply(self):
		if self.parent:
			return True
		else:
			return False
			
	@staticmethod
	def get_comments_for_chunk(chunk):
		all_comments = []
		parent_comments=Comment.objects.filter(chunk=chunk).filter(parent=None)
		for parent_comment in parent_comments:
			temp_stack = [parent_comment]
			while len(temp_stack) != 0:
				temp_child = temp_stack.pop(0)
				all_comments.append(temp_child)
				temp_stack = list(temp_child.child_comments.all()) + temp_stack
		return all_comments

	class Meta:
		ordering = [ 'start', 'end' ]

class Vote(models.Model):
	VALUE_CHOICES = (
		(1, '+1'),
		(-1, '-1'),
	)
	value = models.SmallIntegerField(choices=VALUE_CHOICES)
	comment = models.ForeignKey(Comment, related_name='votes')
	author = models.ForeignKey(User, related_name='votes')

	class Meta:
		unique_together = ('comment', 'author',)

class Star(models.Model):
	value = models.BooleanField(default = False)
	chunk = models.ForeignKey(Chunk, related_name = "stars")
	author = models.ForeignKey(User, related_name = "stars")
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)