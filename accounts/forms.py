from django.contrib import auth

from django.forms import ModelForm, Form
from django.forms import Textarea, HiddenInput, ChoiceField, CharField, EmailField, URLField, ModelChoiceField
from accounts.models import UserProfile
from chunks.models import Semester

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

class UserProfileForm(ModelForm):
    first_name = CharField(label=('First Name'), max_length=30)
    last_name = CharField(label=('Last Name'), max_length=30)
    email = EmailField()

    class Meta:
        model = UserProfile
        fields = ('twitter', 'github', 'website', 'linkedin','photo','about',)

    def __init__(self, *args, **kw):
        super(UserProfileForm, self).__init__(*args, **kw)
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['email'].initial = self.instance.user.email

        self.fields.keyOrder = [
            'first_name',
            'last_name',
            'email',
            'photo',
            'about',
            'twitter',
            'github',
            'website',
            'linkedin',
            ]

    def save(self, *args, **kw):
        super(UserProfileForm, self).save(*args, **kw)
        self.instance.user.first_name = self.cleaned_data.get('first_name')
        self.instance.user.last_name = self.cleaned_data.get('last_name')
        self.instance.user.email = self.cleaned_data.get('email')
        self.instance.user.save()

class UserBulkAddForm(Form):
  users = CharField(widget=Textarea(attrs={'cols': 10, 'rows': 10}))
  semester = ModelChoiceField(queryset=Semester.objects.all())
