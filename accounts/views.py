from accounts.forms import *

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponseRedirect
from limit_registration import check_email, send_email, verify_token
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import Token, UserProfile, Member
from accounts.forms import ReputationForm
from chunks.models import Semester
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
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

def registration_request (request):
    if request.method == 'GET':
        return render(request, 'accounts/registration_request.html')
    else:
        redirect_to = request.POST.get('next', '/')
        #check if the email is a valid alum email
        email = request.POST['email']
        valid_email = check_email(email)
        if valid_email == True:
            # should send out an email with SHA hash as token
            # redirect to some sort of success page
            send_email(email, request)
            return render(request, 'accounts/registration_request_complete.html')
    return render(request, 'accounts/invalidreg.html', {
        'next': redirect_to,
        'invalid_invitation': valid_email
    })

def register(request, email, code):
    invalid_invitation = ""
    if not verify_token(email, code):
        invalid_invitation = "Sorry, this invitation link is invalid."
        return render(request, 'accounts/invalidreg.html', {
            'invalid_invitation': invalid_invitation,
        })
    if request.method == 'GET':
        redirect_to = request.GET.get('next', '/')
        # render a registration form
        form = UserForm(initial={'email': email, 'username':email.replace("@alum.mit.edu", "")})
    else:
        # create a new user
        form = UserForm(request.POST)
        redirect_to = '/'
        if form.is_valid():
            user = form.save()
            username = request.POST['username']
            password = request.POST['password1']
            user = authenticate(username=username, password=password)
            redirect_to = '/'
            if user is not None:
                if user.is_active:
                    user.profile.role = 'A'
                    user.profile.save()
                    auth.login(request, user)
                    return redirect(redirect_to)
            else:
                return redirect('/')
    return render(request, 'accounts/register.html', {
        'form': form,
        'next': redirect_to,
        'invalid_invitation': invalid_invitation,
        'email': email
    })

@login_required
def edit_membership(request):
    """Allow users to enroll in classes."""
    user = request.user
    enrolled_classes = request.user.membership

    if request.method == "POST":
        # handle ajax post to this url
        semester_id = request.POST['semester_id']
        semester = Semester.objects.get(pk=semester_id)

        if request.POST['enrolled']=='True':
            m = request.user.membership.filter(semester=semester)
            m.delete()
        else:
            m = Member(user=request.user, role='volunteer', semester=semester)
            m.save()

    return render(request, 'accounts/edit_membership.html', {
        'semesters': Semester.objects.filter(is_current_semester=True),
        'enrolled_classes': enrolled_classes,
    })

@staff_member_required
def bulk_add(request):
  if request.method == 'GET':
    form = UserBulkAddForm()
    return render(request, 'accounts/bulk_add_form.html', {
      'form': form
    })
  else: # bulk adding time
    form = UserBulkAddForm(request.POST)
    if not form.is_valid():
      return render(request, 'accounts/bulk_add_form.html', {
        'form': form,
        'message': 'Invalid form. Are you missing a field?'})

    # todo(mglidden): use a regex instead of three replace statements
    users = form.cleaned_data['users'].replace(' ', ',').replace('\t', ',').replace('\r\n', ',').replace('\n', ',').replace(', ', ',').split(',')

    semester = form.cleaned_data['semester']

    existing_users = 0; created_users = 0; existing_memberships = 0; created_memberships = 0;

    for user_str in users:
      if '@' in user_str:
        user_email = user_str
        user_str = user_email[:user_email.index('@')]
      else:
        user_email = user_str + '@mit.edu'

      # In production, we should never have more than one user for a given email. The dev DB has some bad data, so we're using filter instead of get.
      # We filter by username since that's the unique key.
      users = User.objects.filter(username=user_str)
      if users:
        user = users[0]
        existing_users += 1
      else:
        user = User(username=user_str, email=user_email)
        user.save()
        user.profile.role = 'S'
        user.profile.save()
        created_users += 1

      if not user.membership.filter(semester=semester):
        membership = Member(role='S', user=user, semester=semester)
        membership.save()
        created_memberships += 1
      else:
        existing_memberships += 1

    return render(request, 'accounts/bulk_add_form.html', {
      'form': form,
      'message': 'Created %s users, %s already existed. Added %s users to %s, %s were already members.' % (created_users, existing_users, created_memberships, semester, existing_memberships),
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
