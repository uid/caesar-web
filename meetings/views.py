from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from scheduler.models import  Meeting, UserProfile
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelForm
from django import forms
from urllib import urlopen, urlencode
import datetime
from random import sample
from string import ascii_uppercase, digits
from WebexMeetingScheduler import settings
import xml.etree.ElementTree as ET
from splitselectdatetimewidget import SplitSelectDateTimeWidget, SelectTimeWidget
from django.utils.safestring import mark_safe
from django_select2.fields import ModelSelect2MultipleField

@login_required
def index(request):
    response = HttpResponse()
    response.write('<a href="/schedule/">Schedule Meeting</a>')
    response.write('<br/>')
    response.write('<a href="/view/">View Meetings</a>')
    return response

class MeetingForm(ModelForm):
    meeting_name = forms.CharField(label='Meeting Name', initial='Code Review Meeting')
    #users = forms.ModelMultipleChoiceField(queryset=UserProfile.objects.all(), label='Attendees')
    users = ModelSelect2MultipleField(queryset=UserProfile.objects, label='Attendees')
    #users = forms.ModelMultipleChoiceField(queryset=UserProfile.objects.all(), widget=FilteredSelectMultiple(('Attendees'), is_stacked=False))
    today = datetime.date.today
#    meeting_start_datetime = forms.DateTimeField(widget=SplitSelectDateTimeWidget(twelve_hr=True, minute_step=15),
#                                       label='Meeting Date and Time',
#                                       initial=lambda:(datetime.datetime.now().replace(hour=17, minute=0,second=0)))
    meeting_start_date = forms.DateField(widget=forms.DateInput(format='%m/%d/%Y', attrs={'class':'datePicker', 'readonly':'true'}),
                                         label='Meeting Date', initial = datetime.date.today)
    meeting_start_time = forms.TimeField(widget = SelectTimeWidget(twelve_hr=True, minute_step=15), label='Meeting Start Time',
                                         initial = datetime.time(hour=17, minute=0, second =0))
    meeting_duration = forms.IntegerField(label='Duration (Minutes)', initial=60)
    
    class Meta:
        model = Meeting
        fields = ('meeting_name', 'users', 'meeting_duration')
        widgets = {
                   #'users': forms.SelectMultiple(attrs={'class':'chosenSelectMultiple',})
                   }
#    class Media:
#        js = ('http://code.jquery.com/jquery-1.6.4.min.js','/static/admin/js/jquery.init.js',)
    
    class Media:
        css = {
            'all':('/static/admin/css/base.css', '/static/admin/css/forms.css', '/static/admin/css/widgets.css'),
        }
        js = ('/static/js/jsi18n.js', '/static/admin/js/jquery.min.js',
              '/static/admin/js/jquery.init.js', '/static/admin/js/actions.min.js', 
              '/static/admin/js/admin/RelatedObjectLookups.js')
#        

@login_required
def schedule(request):
    if request.POST:
        meeting_form = MeetingForm(request.POST)
        m = meeting_form.save(commit=False)   
        
        m.meeting_password = ''.join(sample(ascii_uppercase + digits, 6))
        m.meeting_start_datetime = datetime.datetime.combine(meeting_form.cleaned_data['meeting_start_date'],
                                                             meeting_form.cleaned_data['meeting_start_time'])
        m.meeting_end_datetime = m.meeting_start_datetime + datetime.timedelta(minutes=m.meeting_duration)
              
        cmXML = render_to_string('createmeeting.xml', {
            'meeting': m,
            'user':request.user,
            'attendees': [profile.user for profile in meeting_form.cleaned_data['users']]
        })
        print cmXML
        f = urlopen('http://mit.webex.com/WBXService/XMLService', urlencode({'XML':cmXML}))
        responseXML = ''.join(f.readlines())
        print responseXML
        response_root = ET.fromstring(responseXML)
        result = response_root.find('.//{http://www.webex.com/schemas/2002/06/service}result').text
        
        if result == 'SUCCESS':
            m.meeting_key = response_root.find('.//{http://www.webex.com/schemas/2002/06/service/meeting}meetingkey').text
            m.meeting_attendee_url = "https://mit.webex.com/mit/m.php?AT=JM&AS=AppView&MK=" + m.meeting_key + "&PW=" + m.meeting_password
            jmXML = render_to_string('getjoinurlmeeting.xml', {
                'meeting_key': m.meeting_key,
            })
            print jmXML
            f = urlopen('http://mit.webex.com/WBXService/XMLService', urlencode({'XML':jmXML}))
            responseXML = ''.join(f.readlines())
            print responseXML
            response_root = ET.fromstring(responseXML)
            result = response_root.find('.//{http://www.webex.com/schemas/2002/06/service}result').text
            if result == 'SUCCESS':
                m.meeting_host_url = response_root.find('.//{http://www.webex.com/schemas/2002/06/service/meeting}inviteMeetingURL').text
                m.save()
                meeting_form.save_m2m()            
            return HttpResponseRedirect('/view/')    
        elif result == 'FAILURE':
            raise Exception()
        else:
            raise Exception()
    else:
        meeting_form = MeetingForm(initial={'users': [request.user.profile]})
        return render_to_response('schedule.html', {'meeting_form':meeting_form}, context_instance=RequestContext(request))
    
@login_required
def view(request):
    meeting_map = [(m,m.get_url(request.user)) for m in request.user.profile.get_scheduled_meetings()]
    meeting_map_items = sorted(meeting_map, key=lambda t: t[0].meeting_start_datetime)
    return render_to_response('view.html', {'meeting_map_items': meeting_map_items})

@login_required
def delete(request, meeting_key):
    try:
        meeting = Meeting.objects.get(meeting_key=meeting_key)
        dmXML = render_to_string('deletemeeting.xml', {
            'meeting_key': meeting_key,
        })
        print dmXML
        f = urlopen('http://mit.webex.com/WBXService/XMLService', urlencode({'XML':dmXML}))
        responseXML = ''.join(f.readlines())
        print responseXML
        response_root = ET.fromstring(responseXML)
        result = response_root.find('.//{http://www.webex.com/schemas/2002/06/service}result').text
        
        if result == 'SUCCESS':
            meeting.delete()
        elif result == 'FAILURE':
            raise Exception()
        else:
            raise Exception()
        Meeting.objects.get(meeting_key=meeting_key).delete()
        return HttpResponseRedirect('/view/')    
    except Meeting.DoesNotExist:
        return HttpResponseRedirect('/view/')    
    
@login_required
def edit(request, meeting_key):
    if request.POST:
        try:
            print "boop"
            meeting = Meeting.objects.get(meeting_key=meeting_key)
            print "foop"
            meeting_form = MeetingForm(request.POST, instance = meeting)
            m = meeting_form.save(commit=False)
            m.meeting_start_datetime = datetime.datetime.combine(meeting_form.cleaned_data['meeting_start_date'],
                                                                 meeting_form.cleaned_data['meeting_start_time'])
            m.meeting_end_datetime = m.meeting_start_datetime + datetime.timedelta(minutes=m.meeting_duration)
                  
            smXML = render_to_string('setmeeting.xml', {
                'meeting': m,
                'user':request.user,
                'attendees': [profile.user for profile in meeting_form.cleaned_data['users']]
            })
            print smXML
            f = urlopen('http://mit.webex.com/WBXService/XMLService', urlencode({'XML':smXML}))
            responseXML = ''.join(f.readlines())
            print responseXML
            response_root = ET.fromstring(responseXML)
            result = response_root.find('.//{http://www.webex.com/schemas/2002/06/service}result').text
            
            if result == 'SUCCESS':
                print "successs"
                #Meeting.objects.get(meeting_key=meeting_key).delete()
                m.save()
                meeting_form.save_m2m()
            elif result == 'FAILURE':
                raise Exception()
            else:
                raise Exception()
        except Meeting.DoesNotExist:
            return HttpResponseRedirect('/view/')
        return HttpResponseRedirect('/view/')    
    else:
        try:
            meeting = Meeting.objects.get(meeting_key=meeting_key)
            start_date = meeting.meeting_start_datetime.date()
            start_time = meeting.meeting_start_datetime.time()
            meeting_form = MeetingForm(instance = meeting, initial={'meeting_start_date':start_date, 'meeting_start_time':start_time})
            return render_to_response('edit.html', {'meeting_form':meeting_form, 'meeting':meeting}, context_instance=RequestContext(request))
        except Meeting.DoesNotExist:
            return view(request)
    
