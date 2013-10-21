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
from accounts.models import UserProfile, Member, Extension
from accounts.forms import ReputationForm
from chunks.models import Semester, Submission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import datetime
import sys
import re

from PIL import Image as PImage
from os.path import join as pjoin
from django.conf import settings
from chunks.models import Milestone,SubmitMilestone,ReviewMilestone
from review.models import Comment, Vote

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

@login_required
def view_profile(request, username):
    try:
        participant = User.objects.get(username__exact=username)
    except:
        raise Http404
    review_milestone_data = []
    #get all review milestones
    review_milestones = ReviewMilestone.objects.all().order_by('-assigned_date')
    # turn off Publishing until it's ready
    #submissions = Submission.objects.filter(authors=participant).filter(published=True)
    for review_milestone in review_milestones:
        #get all comments that the user wrote
        comments = Comment.objects.filter(author=participant) \
                          .filter(chunk__file__submission__milestone= review_milestone.submit_milestone).select_related('chunk')
        review_data = []
        for comment in comments:
            if comment.is_reply():
                #false means not a vote activity
                review_data.append(("reply-comment", comment, comment.generate_snippet(), False, None))
            else:
                review_data.append(("new-comment", comment, comment.generate_snippet(), False, None))

        votes = Vote.objects.filter(author=participant) \
                    .filter(comment__chunk__file__submission__milestone = review_milestone.submit_milestone) \
                    .select_related('comment__chunk')
        for vote in votes:
            if vote.value == 1:
                #true means vote activity
                review_data.append(("vote-up", vote.comment, vote.comment.generate_snippet(), True, vote))
            elif vote.value == -1:
                review_data.append(("vote-down", vote.comment, vote.comment.generate_snippet(), True, vote))
        review_data = sorted(review_data, key=lambda element: element[1].modified, reverse = True)
        review_milestone_data.append((review_milestone, review_data))
    return render(request, 'accounts/view_profile.html', {
        'review_milestone_data': review_milestone_data,
        'participant': participant,
#        'submissions': submissions,  turn off Publishing until it's ready
    })

@login_required
def edit_profile(request, username):
    # can't edit if not current user
    if request.user.username != username:
        return redirect(reverse('accounts.views.view_profile', args=([username])))
    """Edit user profile."""
    profile = User.objects.get(username=username).profile
    photo = None
    img = None
    if profile.photo:
        photo = profile.photo.url
    else:
        photo = "http://placehold.it/180x144&text=Student"

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            if request.FILES:
                # resize and save image under same filename
                imfn = pjoin(settings.MEDIA_ROOT, profile.photo.name)
                im = PImage.open(imfn)
                im.thumbnail((180,180), PImage.ANTIALIAS)
                im.save(imfn, "PNG")
            return redirect(reverse('accounts.views.view_profile', args=([username])))
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'photo': photo,
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

@login_required
def allusers(request):
    participants = User.objects.all().exclude(username = 'checkstyle').select_related('profile').order_by('last_name')
    print participants
    return render(request, 'accounts/allusers.html', {
        'participants': participants,
    })

@login_required
def request_extension(request, milestone_id):
    user = request.user

    # what semester is this milestone in?
    current_milestone = Milestone.objects.get(id=milestone_id)
    semester = current_milestone.assignment.semester
    membership = Member.objects.get(semester=semester, user=user)

    # calculate how much slack budget user has left for this semester
    slack_budget = membership.slack_budget
    used_slack = sum([extension.slack_used for extension in Extension.objects.filter(user=user, milestone__assignment__semester=semester)])
    total_extension_days_left = slack_budget - used_slack

    # get the user's current personal due date for this assignment (including any existing extension)
    try:
        user_duedate = current_milestone.extensions.get(user=user).new_duedate()
    except ObjectDoesNotExist:
        user_duedate = current_milestone.duedate

    # User is going to request an extension
    if request.method == 'GET':
        current_milestone = Milestone.objects.get(id=milestone_id)
        # Make sure user got here legally
        if datetime.datetime.now() > user_duedate + datetime.timedelta(minutes=30):
            return redirect('dashboard.views.dashboard')

        current_extension = (user_duedate - current_milestone.duedate).days

        late_days = 0
        if datetime.datetime.now() > current_milestone.duedate + datetime.timedelta(minutes=30):
            late_days = (datetime.datetime.now() - current_milestone.duedate + datetime.timedelta(minutes=30)).days + 1

        possible_extensions = range(late_days, min(total_extension_days_left+current_extension+1, current_milestone.max_extension+1))

        written_dates = []
        for day in range(possible_extensions[-1]+1):
            extension = day * datetime.timedelta(days=1)
            written_dates.append(current_milestone.duedate + extension)


        return render(request, 'accounts/extension_form.html', {
            'possible_extensions': possible_extensions,
            'current_extension': current_extension,
            'written_dates': written_dates,
            'total_extension_days': total_extension_days_left + current_extension
        })
    else: # user just submitted an extension request
        days = request.POST.get('dayselect', None)
        try:
            extension_days = int(days)
            current_extension = (user_duedate - current_milestone.duedate).days
            total_extension_days = total_extension_days_left + current_extension

            if extension_days > total_extension_days or extension_days < 0 or extension_days > current_milestone.max_extension:
                return redirect('dashboard.views.dashboard')
            extension,created = Extension.objects.get_or_create(user=user, milestone=current_milestone)
            if extension_days == 0: # Don't keep extensions with 0 slack days
                extension.delete()
            else:
                extension.slack_used = extension_days
                extension.save()
            return redirect('dashboard.views.dashboard')
        except ValueError:
            return redirect('dashboard.views.dashboard')

@staff_member_required
def manage(request):
    return render(request, 'accounts/manage.html', {
    })
