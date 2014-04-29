from review.models import *
from accounts.models import UserProfile

from django.forms import ModelForm, Form
from django.forms import Textarea, HiddenInput, ChoiceField, CharField

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'start', 'end', 'chunk')
        widgets = {
            'text': Textarea(attrs={'cols': 10, 'rows': 5, 'id': 'textentry', 'style': 'display: block'}), 
            'start': HiddenInput(),
            'end': HiddenInput(),
            'chunk': HiddenInput(),
        }

class ReplyForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'parent')
        widgets = {
            'text': Textarea(attrs={'cols': 10, 'rows': 5}), 
            'parent': HiddenInput(),
        }

class EditCommentForm(Form):
    text = CharField(widget=Textarea(attrs={'cols': 10, 'rows': 5}))
    comment_id = CharField(widget=HiddenInput())