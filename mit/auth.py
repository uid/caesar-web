# Code courtesy of Alex Dehnert <adehnert@mit.edu>
import ldap
import ldap.filter
import sys

from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist

class SSLRemoteUserMiddleware(RemoteUserMiddleware):
    header = 'SSL_CLIENT_S_DN_Email'

class SSLRemoteUserBackend(RemoteUserBackend):
    def clean_username(self, username, ):
        if '@' in username:
            name, domain = username.split('@')
            assert domain.upper() == 'MIT.EDU'
            return name
        else:
            return username
    def configure_user(self, user, ):
        username = user.username
        user.set_unusable_password()
        con = ldap.open('ldap.mit.edu')
        con.simple_bind_s("", "")
        dn = "dc=mit,dc=edu"
        fields = ['cn', 'sn', 'givenName', 'mail', ]
        userfilter = ldap.filter.filter_format('uid=%s', [username])
        result = con.search_s('dc=mit,dc=edu', ldap.SCOPE_SUBTREE, userfilter, fields)
        if len(result) == 1:
            user.first_name = result[0][1]['givenName'][0]
            user.last_name = result[0][1]['sn'][0]
            user.email = result[0][1]['mail'][0]
            try:
                user.groups.add(auth.models.Group.objects.get(name='MIT'))
            except ObjectDoesNotExist:
                print "Failed to retrieve mit group"
        else:
            raise ValueError, ("Could not find user with username '%s' (filter '%s')"%(username, userfilter))
        try:
            user.groups.add(auth.models.Group.objects.get(name='autocreated'))
        except ObjectDoesNotExist:
            print "Failed to retrieve autocreated group"
        user.save()
        return user
