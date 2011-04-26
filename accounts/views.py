from caesar.accounts.forms import *

from django.views.generic.simple import direct_to_template
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate 
from django.contrib import auth
from django.shortcuts import redirect
from django.http import HttpResponseRedirect

def login(request):
    if request.method == 'GET':
        redirect_to = request.GET['next']
        if request.is_ajax():
            return direct_to_template(request, 'accounts/login_fragment.html', {
                'form': AuthenticationForm(),
                'next': redirect_to
            })
    else:
        redirect_to = request.POST['next']
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(redirect_to)
        return direct_to_template(request, 'accounts/login.html', {
            'form': form,
            'next': redirect_to
        })

def register(request):
    redirect_to = request.REQUEST.get('next', '')
    if request.method == 'POST':
        # create a new user
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            return HttpResponseRedirect(redirect_to)
    else:
        # render a registration form
        form = UserForm()
    return direct_to_template(request, 'accounts/register.html', {
        'form': form,
        'next': redirect_to
    })

