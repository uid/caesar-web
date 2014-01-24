Requirements
============
* Ubuntu or Debian
* Python 2.7 with `pip` available
* Apache 2 with `mod_wsgi` and `mod_ssl`

All of the configuration files expect the project code to live at 
`/var/django/caesar`.


Development
============

We use Vagrant and VirtualBox to run Caesar in a virtual machine on your laptop.  Here are the steps:

### Clone from github

Clone this repository from github.

    git clone https://github.com/uid/caesar-web.git
    cd caesar-web

### Configure local settings

Copy the template for settings_local.py:

    cp settings_local.py.template settings_local.py

The default settings are intended for development: DEBUG is turned on, a local sqlite database file is used for storing data.  For deploying Caesar as a user-facing web app, you should edit settings_local.py and change settings as explained by the comments.

### Use Vagrant to start the virtual machine

Install [Vagrant](http://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org) on your laptop.

Make sure you're in your caesar-web folder, which has the Vagrantfile in it.  Start the VM:

    vagrant up

Log into it:

    vagrant ssh

On the VM, run the setup script:

    cd /var/django/caesar
    sudo ./setup.sh

The setup script will probably stop to ask you to configure postfix.  Use the defaults (Internet Site, hostname precise32).

Ignore the final warning from apache2: Could not reliably determine the server's fully qualified domain name.

### Initialize Caesar

First collect static assets:

    cd /var/django/caesar
    ./manage.py collectstatic

Now initialize the database.  With the default settings_local.py file, the database is stored in a .sqlite3 file in fixtures/, so you can always delete that file and start this part over if things go wrong. 

    ./manage.py syncdb         # say "no", don't create superuser yet
    ./manage.py migrate

Create a superuser that will allow you to log in to Caesar with admin privileges:

    ./manage.py createsuperuser

Preload the database with test data:

    ./manage.py loaddata fixtures/test_fixtures.json

Finally, make sure the Apache server can write to the database:

    chmod -R g+w fixtures/ 
    chgrp -R www-data fixtures/

### Test that Caesar is running

Browse to [10.18.6.30](http://10.18.6.30) on your laptop and try to log in, either using the superuser
account you created above, or (if you're at MIT) with your MIT certificate.  If login is successful, clicking on the "view all users" link at the top of the page should show you all the users in the test database.


### Development tips

To edit code, work with git, and use other dev tools, just work with the caesar-web folder that you checked out to your laptop.  This folder tree is synced automatically with /var/django/caesar in the VM.  You don't have to go inside the VM.

The only thing you *do* have to do from the VM is restart Apache whenever you edit a Python source file.  Here's how:

    vagrant ssh              # if you're not already logged into your VM
    sudo apachectl graceful  # to restart Apache and force it to reload Caesar

The Django debug toolbar ("DjDt") appears on the right side of Caesar's web pages whenever you have DEBUG=True in settings_local.py.  The toolbar is particularly useful for viewing debug messages. To print messages, use

    import logging
    logging.debug("hello, world")

Messages like this will appear in the Logging pane of the debug toolbar.



Deployment
==========

Ubuntu
------
Before doing anything, make sure you have a few packages installed:

    sudo aptitude install libldap2-dev python-numpy python-psycopg2 postfix

Configuring SSL is a bit trickier, but assuming you already have `mod_ssl` 
installed and your working directory is the project root:

    sudo a2enmod ssl
    cd /var/django/caesar
    sudo cp apache/mitCAclient.pem /etc/ssl/certs/
    cd /etc/apache2/sites-enabled
    sudo ln -s ../sites-available/default-ssl 000-default-ssl 

The fabfile should take care of the rest, in theory.

Enable JPEG and PNG support for photos:

    pip uninstall PIL
    sudo apt-get install libjpeg-dev libfreetype6 libfreetype6-dev zlib1g-dev
    sudo ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/
    sudo ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/
    sudo ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/
    pip install PIL

The install script should now display at the end:

    --------------------------------------------------------------------
    *** TKINTER support not available
    --- JPEG support available
    --- ZLIB (PNG/ZIP) support available
    --- FREETYPE2 support available
    *** LITTLECMS support not available
    --------------------------------------------------------------------


CSAIL Debian Lenny
------------------

### Installing build dependencies
Before we get started, you will need a few things:

    sudo aptitude install apache2 apache2-dev libldap2-dev libsasl2-dev git

### Building Python 2.7
CSAIL's distribution of Debian includes only Python 2.6, which isn't going to 
be good enough for our purposes, so we'll have to install Python 2.7 from 
source alongside the existing Python installation.

    wget http://www.python.org/ftp/python/2.7.2/Python-2.7.2.tgz
    tar xvzf Python-2.7.2.tgz
    cd Python-2.7.2
    ./configure --with-threads --enable-shared
    make
    sudo make altinstall
    sudo ln -s /usr/local/lib/libpython2.7.so.1.0 /usr/lib/
    sudo ln -s /usr/local/lib/libpython2.7.so /usr/

Next, we also need to install `setuptools` and `pip` for our shiny new Python.

    wget http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg
    sudo sh setuptools-0.6c11-py2.7.egg
    sudo easy_install-2.7 pip

### Building mod_wsgi
To actually run Caesar on `mod_wsgi` with Python 2.7 instead of 2.5, we need to
compile our own binary for the module against our new Python binary. We will
also hand-install the compiled binary alongside any existing files from the
packaged version of `mod_wsgi`.

    sudo aptitude install libapache2-mod-wsgi
    wget http://modwsgi.googlecode.com/files/mod_wsgi-3.3.tar.gz
    tar xvzf mod_wsgi-3.3.tar.gz
    cd mod_wsgi-3.3
    ./configure --with-python=/usr/local/bin/python2.7
    make
    sudo cp .libs/mod_wsgi.so /usr/lib/apache2/modules/mod_wsgi.so-2.7
    cd /usr/lib/apache2/modules
    sudo ln -sf mod_wsgi.so-2.7 mod_wsgi.so

### Configuring Apache
To make sure that `mod_wsgi` is pointed to the right Python installation, you
will need to add one line to `/etc/apache2/mods-available/wsgi.conf`.

    <IfModule mod_wsgi.c>
        ...
        WSGIPythonHome /usr/local
        ...
    </IfModule> 

Finally make sure the module is enabled:

    sudo a2enmod wsgi

The default configuration included with Caesar assumes that the WSGI daemon will
run under the `caesar` user, which you will probably need to create. It will
also help to create a user group with the newly created `caesar` user, the 
Apache user, and yourself:

    sudo useradd -r caesar
    sudo groupadd dev
    sudo adduser caesar dev
    sudo adduser $USER dev
    sudo adduser www-data dev

### Check out Caesar
Now, checkout the code (creating any necessary directories). Caesar assumes that
it will live at `/var/django/caesar`:

    sudo mkdir -p /var/django/caesar
    cd /var/django/caesar
    sudo chgrp dev .
    sudo chown $USER .
    sudo chmod g+w .
    sudo chmod g+s .
    cd ..
    git clone git://github.com/uid/caesar-web.git caesar

### Enable SSL
Next, set up `mod_ssl` and add the appropriate MIT certificate authority:

    sudo a2enmod ssl
    sudo cp /var/django/caesar/apache/mitCAclient.pem /etc/ssl/certs/
    cd /etc/apache2/sites-enabled
    sudo ln -s ../sites-available/default-ssl 000-default-ssl 

Make sure that Apache actually listens to the SSL port, too

    grep Listen /etc/apache2/ports.conf
    
If you don't see both "Listen: 80" and "Listen: 443" in the output of this command, then
you need to edit /etc/apache2/ports.conf to include Listen: 443.  Here's a suggested block to
add to the file:

    <IfModule mod_ssl.c>
        Listen 443
    </IfModule>


### Installing Python dependencies
To install Caesar's Python dependencies, just run:

    cd /var/django/caesar
    sudo pip-2.7 install -r requirements.txt
    
Note: This may not install ldap correctly if you're running OS X. If importing ldap causes errors, run:

    pip-2.7 install python-ldap==2.3.13
    easy_install-2.7 ElementTree
    easy_install-2.7 Markdown 

You also need to install django_tools.middlewares by placing the django_tools
folder (obtainable from https://github.com/jedie/django-tools/tree/master/django_tools)
into a python2.7 path folder. To find a python2.7 path folder run python2.7, import sys,
and then print sys.path. Put the django_tools folder in one of the folders in the sys.path
list. Verify that its working by running python2.7 and trying to import django_tools.middlewares.ThreadLocal

### Configuring Caesar

To point Caesar to the right database, copy the local settings file:

    cd /var/django/caesar
    cp settings_local.py.template settings_local.py

Then edit settings_local.py and change the settings appropriately.


### Initializing the application

Finally, Caesar itself needs some setup:
Note: when running ./manage.py syncdb, Django may ask if you want to create a new superuser for it's auth system. Select 'no' - the users table doesn't exist until migrate, so this will cause an error.

    cd /var/django/caesar
    mkdir media && chmod g+w media
    ./manage.py syncdb
    ./manage.py migrate
    ./manage.py createsuperuser --username=admin --email=example@mit.edu
    ./manage.py collectstatic
    sudo ln -sf /var/django/caesar/apache/caesar /etc/apache2/sites-available
    sudo a2ensite caesar
    sudo /etc/init.d/apache2 restart

### Enable JPEG and PNG support for photos:

    pip uninstall PIL
    sudo apt-get install libjpeg-dev libfreetype6 libfreetype6-dev zlib1g-dev
    sudo ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/
    sudo ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/
    sudo ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/
    pip install PIL

The install script should now display at the end:

    --------------------------------------------------------------------
    *** TKINTER support not available
    --- JPEG support available
    --- ZLIB (PNG/ZIP) support available
    --- FREETYPE2 support available
    *** LITTLECMS support not available
    --------------------------------------------------------------------

To run Caesar in debug mode, use the following command:
    python -m pdb manage.py runserver localhost:8888

This will cause Django to automatically reload all altered code. Additionally, by using:
    import pdb; pdb.set_trace()
you can drop down into a PBD session (incredibly useful for debugging crashes & bugs)
