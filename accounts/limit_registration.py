import settings
from re import match
from django.core.mail import EmailMultiAlternatives
from hashlib import md5
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from urllib import quote_plus, unquote_plus
from django.contrib.auth.models import User

def get_names():
    f = open(settings.project_path('accounts') + '/second-wave-alums.txt')
    user_parts = []
    for line in f:
        user_line = line.split()
        for part in user_line:
            comma = part.find(',')
            if comma != -1:
                user_parts.append(part[0:comma].lower())
            else:
                user_parts.append(part.lower())

    return user_parts

def check_name(first, last, email, username):
    user_parts = get_names()
    if email.lower() in user_parts:
        return True
    if first.lower() in user_parts or last.lower() in user_parts or username.lower() in user_parts:
        return True
    return False

# also ensure that this email isn't in the system already
def check_email(email):
    # if actually an ___@alum.mit.edu address
    if match("^[a-zA-Z0-9._%-+]+@alum\.mit\.edu$", email) == None:
        return 'You need a valid @alum.mit.edu address to register.'
    # if that email isn't in the system yet
    if len(User.objects.filter(email=email)) != 0:
        return 'That email has been registered already.'
    return True

def send_email(email):
    token = md5("Nobody inspects the spammish repetition"+email).hexdigest()

    subject, from_email, to = 'Caesar registration request', 'admin@caesar.com', email
    url = ''.join(['http://',Site.objects.get_current().domain,\
            reverse('accounts.views.register', args=(quote_plus(email), token))])
    text_body = 'Sign up at '+url
    html_body = 'Sign up at <a href="'+url+'">this link</a>.'

    msg = EmailMultiAlternatives(subject, text_body, from_email, [to])
    msg.attach_alternative(html_body, "text/html")
    msg.send()
    return True

def verify_token(email, token):
    token_check = md5("Nobody inspects the spammish repetition"+unquote_plus(email)).hexdigest()
    return token == token_check and len(User.objects.filter(email=email)) == 0
