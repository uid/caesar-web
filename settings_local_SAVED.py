DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'caesar_dev',         # Or path to database file if using sqlite3.
        'USER': 'caesar',                      # Not used with sqlite3.
        'PASSWORD': 'OJ1kYVQ',                  # Not used with sqlite3.
        'HOST': 'mysql.csail.mit.edu',                      # Set to empty strin
        'PORT': '',                      # Set to empty string for default. Not
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'r0xlpq%j!slk%^po8125pc&s=u%t_5u%_m8%7y3)m()x$$%4o2'

