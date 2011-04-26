from django import forms
from django.contrib import auth

class UserForm(auth.forms.UserCreationForm):
    username = forms.CharField(max_length=8, 
            help_text='Please use your Athena username if you have one.')
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    class Meta(auth.forms.UserCreationForm.Meta):
        fields = ('username', 'first_name', 'last_name', 'email',)


