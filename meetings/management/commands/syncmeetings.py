from django.core.management.base import BaseCommand
from scheduler.models import Meeting
from django.template.loader import render_to_string
from urllib import urlopen, urlencode
import datetime
import xml.etree.ElementTree as ET

class Command(BaseCommand):
    help = 'Sync the locally stored meetings with the Webex meetings'
    
    def handle(self, *args, **options):
        MEET_PREFIX = './/{http://www.webex.com/schemas/2002/06/service/meeting}'
        
        endDateStart = datetime.datetime.now() - datetime.timedelta(minutes=30)
        cmXML = render_to_string('lstsummarymeeting.xml', {
            'endDateStart': endDateStart,
        })
        print cmXML
        f = urlopen('http://mitweb.webex.com/WBXService/XMLService', urlencode({'XML':cmXML}))
        responseXML = ''.join(f.readlines())
        print responseXML
        response_root = ET.fromstring(responseXML)
        result = response_root.find('.//{http://www.webex.com/schemas/2002/06/service}result').text
        if result == 'SUCCESS':
            meetingElements = response_root.findall(MEET_PREFIX + 'meeting')
            
            meeting_statuses = {}
            for meetingElement in meetingElements:
                meeting_key = meetingElement.find(MEET_PREFIX + 'meetingKey').text
                meeting_status = meetingElement.find(MEET_PREFIX + 'status').text
                meeting_statuses[meeting_key] = meeting_status
            
            for meeting in Meeting.objects.exclude(meeting_status='F').exclude(meeting_status='D'):
                if meeting.meeting_key in meeting_statuses:
                    if meeting_statuses[meeting.meeting_key] == 'NOT_INPROGRESS':
                        meeting.meeting_status = 'S'
                        self.stdout.write('Meeting '+meeting.meeting_name+' not in progress\n')

                    elif meeting_statuses[meeting.meeting_key] == 'INPROGRESS':
                        self.stdout.write('Meeting '+meeting.meeting_name+' in progress\n')
                        meeting.meeting_status = 'I'
                    else:
                        raise Exception();
                else:
                    meeting.meeting_status = 'F'
                    self.stdout.write('Meeting '+meeting.meeting_name+' finished\n')
                meeting.save();        
            self.stdout.write('Meetings are synchronized\n')
        elif result == 'FAILURE':
            raise Exception()
        else:
            raise Exception()
            
