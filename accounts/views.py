from accounts.forms import *

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate 
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponseRedirect
from limit_registration import check_name
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import Token
from accounts.models import UserProfile
from accounts.forms import ReputationForm
import datetime
import sys
import re

def login(request):
    if request.method == 'GET':
        redirect_to = request.GET.get('next', '/')
        return render(request, 'accounts/login.html', {
            'form': AuthenticationForm(),
            'next': redirect_to
        })
    else:
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return HttpResponseRedirect(redirect_to)
            
        redirect_to = request.POST.get('next', '/')
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(redirect_to)
        return render(request, 'accounts/login.html', {
            'form': form,
            'next': redirect_to
        })
def invalid_registration(request):
    invalid_invitation = "Sorry, this invitation has expired. "
    return render(request, 'accounts/invalidreg.html', {
        'invalid_invitation': invalid_invitation,
    })
    
def register(request, code):
    sys.stderr.write('In register. \n')
    invalid_invitation = ""
    token = None
    try:
        token = Token.objects.get(code=code)
    except  ObjectDoesNotExist:
        sys.stderr.write('Failed.')
        invalid_invitation = "Sorry, this invitation has expired."
        return render(request, 'accounts/invalidreg.html', {
            'invalid_invitation': invalid_invitation,
        })
    if token.expire < datetime.datetime.now():
        invalid_invitation = "Sorry, this invitation has expired."
        return render(request, 'accounts/invalidreg.html', {
            'invalid_invitation': invalid_invitation,
        })
    if request.method == 'GET':
        redirect_to = request.GET.get('next', '/')
        # render a registration form
        form = UserForm()
    else:
        redirect_to = request.POST.get('next', '/')
        # create a new user
        form = UserForm(request.POST)
        #check if username, first_name, or last_name ar in the list of permitted users
        valid_name = check_name(request.POST['first_name'], request.POST['last_name'], request.POST['email'], request.POST['username'])
        if not valid_name:
            invalid_invitation = "Your name/email does not appear on the invitation list."
        if form.is_valid() and valid_name:
            user = form.save()
        username = request.POST['username']
        password = request.POST['password1']
        user = authenticate(username=username, password=password)
        if user is not None:
            user.profile.token = token
            user.profile.save()
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(redirect_to)
    return render(request, 'accounts/register.html', {
        'form': form,
        'next': redirect_to,
        'invalid_invitation': invalid_invitation
    })
    
@staff_member_required
def reputation_adjustment(request):
    if request.method == 'GET':
        form = ReputationForm()
        return render(request, 'accounts/reputation_form.html', {
            'form': form,
            'empty': True,
            'success': True,
            'err': ""
        })  
    else:
        form = ReputationForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            text.replace('\n', ',')
            pattern = re.compile(r'[\s,]+')
            split_text = pattern.split(text)
            success = True
            err = ""
            if len(split_text) % 2 == 1: #uneven number of tokens
                success = False
                err = "Uneven number of tokens."
            else:
                profiles_to_update = []
                for i in range(0, len(split_text),2):
                    value = 0
                    try:
                        value = int(split_text[i+1])
                    except ValueError:
                        success = False
                        err = str(split_text[i+1]) + " is not an integer."
                        break
                    if re.search('@', split_text[i]): #email
                        try:
                            profile = UserProfile.objects.get(user__email = split_text[i])
                            profiles_to_update.append((profile, value))
                        except ObjectDoesNotExist:
                            success = False
                            err = str(split_text[i]) + " is not a valid email."
                            break
                    else: #assume username
                        try:
                            profile = UserProfile.objects.get(user__username = split_text[i])
                            profiles_to_update.append((profile, value))
                        except ObjectDoesNotExist:
                            success = False
                            err = str(split_text[i]) + " is not a valid username."
                            break
                if success:
                    for profile, value in profiles_to_update:
                        profile.reputation += value
                        profile.save()
                        success = True
            return render(request, 'accounts/reputation_form.html', {
                'form': form,
                'empty': False,
                'success': success,
                'err': err
            })