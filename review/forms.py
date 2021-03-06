from django.contrib import auth
from django.forms import ModelForm, Form
from django.forms import Textarea, HiddenInput, ChoiceField, CharField, EmailField, ModelChoiceField, IntegerField
from django.core.validators import RegexValidator

from review.models import *

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


class UserForm(auth.forms.UserCreationForm):
    username = CharField(max_length=8,
            help_text='Please use your Athena username if you have one.',\
            validators=[RegexValidator(regex=r'^\w+$')],\
            error_messages={'invalid': ('Use only alphanumeric characters and the underscore.')})
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=30)
    email = EmailField()

    class Meta(auth.forms.UserCreationForm.Meta):
        fields = ('username', 'first_name', 'last_name', 'email',)

    def save(self, *args, **kwargs):
        super(UserForm, self).save(*args, **kwargs)
        self.instance.profile.class_year = self.cleaned_data.get('class_year')
        self.instance.profile.save()


class ReputationForm(Form):
    text = CharField(widget=Textarea(attrs={'cols': 10, 'rows': 10}))

class UserProfileForm(ModelForm):
    first_name = CharField(label=('First Name'), max_length=30)
    last_name = CharField(label=('Last Name'), max_length=30)
    email = EmailField()

    class Meta:
        model = UserProfile
        fields = '__all__'

    def __init__(self, *args, **kw):
        super(UserProfileForm, self).__init__(*args, **kw)
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['email'].initial = self.instance.user.email

        self.fields.keyOrder = [
            'first_name',
            'last_name',
            'email',
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

class SimulateRoutingForm(Form):
  num_students = IntegerField()
  num_staff = IntegerField()
  num_alum = IntegerField()
