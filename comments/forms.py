from caesar.comments.models import *

from django.forms import ModelForm
from django.forms import Textarea, HiddenInput

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text','start', 'end')
        widgets = {
            'start': HiddenInput(),
            'end': HiddenInput(),
        }
