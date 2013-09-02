"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase, Client
from chunks.models import Submission, File
from chunks.views import *

class UserTest(TestCase):
    fixtures = ['test_fixtures.json']

    def test_chunks(self):
        """
        Count number of chunks that exist
        """
        # self.assertTrue(Submission.objects.all().count() == 8)

    def test_files(self):
        """
        Count number of submissions that exist
        """
        # self.assertTrue(File.objects.all().count() == 64)

class PublishCodeTest(TestCase):
    fixtures = ['test_fixtures.json']

    def test_publishing(self):
        """
        Tests that an attempt to publish code results in publication.
        """
        c = Client()
        c.login(username='kimdeal', password='test')
        u = User.objects.get(username='kimdeal')
        submission = u.submissions.all()[0]
        c.post('/chunks/publish/', {'submission_id': '472', 'published': 'False'})
        # TODO: test that the submission's published field is now true
        self.assertTrue(submission.published)

    def test_publishing_others(self):
        """
        Tests that an attempt to publish someone else's code results in failure.
        """
        pass
