import os
import sys

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
projpath = path + '/caesar'
if path not in sys.path:
    sys.path.append(path)
    sys.path.append(projpath)

os.environ['DJANGO_SETTINGS_MODULE'] = 'caesar.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

