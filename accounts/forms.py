from django.contrib import auth

from django.forms import ModelForm, Form
from django.forms import Textarea, HiddenInput, ChoiceField, CharField, EmailField

class UserForm(auth.forms.UserCreationForm):
    username = CharField(max_length=8, 
            help_text='Please use your Athena username if you have one.')
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=30)
    email = EmailField()
    class Meta(auth.forms.UserCreationForm.Meta):
        fields = ('username', 'first_name', 'last_name', 'email',)


class ReputationForm(Form):
    text = CharField(widget=Textarea(attrs={'cols': 10, 'rows': 10}))