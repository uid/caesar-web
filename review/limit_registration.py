from re import match
from django.core.mail import EmailMultiAlternatives
from hashlib import md5
from django.core.urlresolvers import reverse
from urllib import quote_plus, unquote_plus
from django.contrib.auth.models import User
from django.conf import settings

# also ensure that this email isn't in the system already
def check_email(email):
    # if actually an ___@alum.mit.edu address
    if match("^[a-zA-Z0-9._%-+]+@alum\.mit\.edu$", email) == None:
        return 'You need a valid @alum.mit.edu address to register.'
    # if that email isn't in the system yet
    if len(User.objects.filter(email=email)) != 0:
        return 'That email has been registered already.'
    return True

def send_email(email, request):
    token = md5(settings.SECRET_KEY+email).hexdigest()

    subject, from_email, to = 'Caesar registration request', 'caesar@csail.mit.edu', email
    url = ''.join([reverse('review.views.register', args=(quote_plus(email), token))])
    url = request.build_absolute_uri(url)
    text_body = 'Sign up at '+url
    html_body = 'Sign up at <a href="'+url+'">this link</a>.'

    msg = EmailMultiAlternatives(subject, text_body, from_email, [to])
    msg.attach_alternative(html_body, "text/html")
    msg.send()
    return True

def verify_token(email, token):
    token_check = md5(settings.SECRET_KEY+unquote_plus(email)).hexdigest()
    return token == token_check and len(User.objects.filter(email=email)) == 0
