from review.models import *

from django.forms import ModelForm
from django.forms import Textarea, HiddenInput

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text','start', 'end', 'chunk')
        widgets = {
            'text': Textarea(attrs={'cols': 10, 'rows': 5}), 
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
