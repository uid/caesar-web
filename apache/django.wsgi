import os
import sys

path = '/home/caesar'
projpath = path + '/caesar'
if path not in sys.path:
    sys.path.append(path)
    sys.path.append(projpath)

os.environ['DJANGO_SETTINGS_MODULE'] = 'caesar.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

