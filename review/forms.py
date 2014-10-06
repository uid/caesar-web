from review.models import *
from accounts.models import UserProfile

from django.forms import ModelForm, Form
from django.forms import Textarea, HiddenInput, ChoiceField, CharField

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'start', 'end', 'chunk', 'similar_comment')
        widgets = {
            'text': Textarea(attrs={'id': 'hidden-textarea'}), 
            'start': HiddenInput(),
            'end': HiddenInput(),
            'chunk': HiddenInput(),
            'similar_comment': HiddenInput(attrs={'id': 'hidden-similar-comment'}),
        }

class ReplyForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'parent', 'similar_comment')
        widgets = {
            'text': Textarea(attrs={'id': 'hidden-textarea'}), 
            'parent': HiddenInput(),
            'similar_comment': HiddenInput(attrs={'id': 'hidden-similar-comment'}),
        }

class EditCommentForm(Form):
    text = CharField(widget=Textarea(attrs={'id': 'hidden-textarea'}))
    comment_id = CharField(widget=HiddenInput())
    similar_comment = CharField(widget=HiddenInput(attrs={'id': 'hidden-similar-comment'}))