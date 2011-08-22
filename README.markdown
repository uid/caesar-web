Requirements
============
* Ubuntu 11.04 or CSAIL Debian
* Python 2.7 with `pip` available
* Apache 2 with `mod_wsgi` and `mod_ssl`

In addition, all of the configuration files expect the project code to live at 
`/var/django/caesar`.

The `requirements.txt` file specifies all Python dependencies with the exception
of LDAP support, which you should install as OS
packages.

Deployment
==========

Ubuntu
------
Before doing anything, make sure you have a few packages installed:

    sudo aptitude install libldap2-dev python-numpy python-psycopg2 postfix

Configuring SSL is a bit trickier, but assuming you already have `mod_ssl` 
installed and your working directory is the project root:

    sudo a2enmod ssl
    sudo cp apache/mitCAclient.pem /etc/ssl/certs/
    cd /etc/apache2/sites-enabled
    sudo ln -s ../sites-available/default-ssl 000-default-ssl 

The fabfile should take care of the rest, in theory.

CSAIL Debian Lenny
------------------

### Installing build dependencies
Before we get started, you will need a few things:

    sudo aptitude install apache2 apache2-dev libldap2-dev

### Building Python 2.7
CSAIL's distribution of Debian includes only Python 2.5, which isn't going to 
be good enough for our purposes, so we'll have to install Python 2.7 from 
source alongside the existing Python installation.

    wget http://www.python.org/ftp/python/2.7.2/Python-2.7.2.tgz
    tar xvzf Python-2.7.2.tgz
    cd Python-2.7.2.tgz
    sudo ./configure --with-threads --enable-shared
    sudo make
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
    cd mod_wsgi-3.3.tar.gz
    sudo ./configure --with-python=/usr/local/bin/python2.7
    sudo make
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

Next, set up `mod_ssl` and add the appropriate MIT certificate authority:

    sudo a2enmod ssl
    sudo cp apache/mitCAclient.pem /etc/ssl/certs/
    cd /etc/apache2/sites-enabled
    sudo ln -s ../sites-available/default-ssl 000-default-ssl 

The default configuration included with Caesar assumes that the WSGI daemon will
run under the `caesar` user, which you will probably need to create. It will
also help to create a user group with the newly created `caesar` user, the 
Apache user, and yourself:

    sudo useradd -r caesar
    sudo groupadd dev
    sudo adduser caesar dev
    sudo adduser $USER dev
    sudo adduser www-data dev

### Installing Python dependencies
To install Caesar's Python dependencies, just run:

    cd /var/django/caesar
    sudo pip-2.7 install -r requirements.txt

### Initializing the application
Now, checkout the code (creating any necessary directories). Caesar assumes that
it will live at `/var/django/caesar`:

    sudo mkdir -p /var/django/caesar
    cd /var/django/caesar
    sudo chgrp dev .
    sudo chmod g+w .
    sudo chmod g+s .
    cd ..
    git clone git://github.com/masont/caesar-web.git caesar

Finally, Caesar itself needs some setup:

    cd /var/django/caesar
    mkdir media && chmod g+w media
    ./manage.py syncdb
    ./manage.py migrate
    ./manage.py collectstatic
    sudo /etc/init.d/apache2 restart

