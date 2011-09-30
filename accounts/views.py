from accounts.forms import *

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate 
from django.contrib import auth
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponseRedirect
from limit_registration import check_name
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import Token
import datetime
import sys

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

