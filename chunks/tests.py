"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from chunks.models import Submission, File

class UserTest(TestCase):
    fixtures = ['test_fixtures.json']

    def test_chunks(self):
        """
        Count number of chunks that exist
        """
        self.assertTrue(Submission.objects.all().count() == 8)

    def test_files(self):
        """
        Count number of submissions that exist
        """
        self.assertTrue(File.objects.all().count() == 64)
