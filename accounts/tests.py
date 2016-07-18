"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from review.models import User

class UserTest(TestCase):
    fixtures = ['test_fixtures.json']

    def test_existence(self):
        """
        Tests that rcm is actually loaded.
        """
        self.assertTrue(User.objects.filter(username='rcm').exists())
