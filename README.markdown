Requirements
============
* Ubuntu 11.04
* Python 2.7 with `pip` available
* Apache 2 with `mod_wsgi` and `mod_ssl`

In addition, all of the configuration files expect the project code to live at 
`/var/django/caesar`.

The `requirements.txt` file specifies all Python dependencies with the exception
of the Python Imaging Library and LDAP support, which you should install as OS
packages.

Deployment
==========
Before doing anything, make sure you have a few packages installed:

    sudo aptitude install python-imaging python-ldap

Configuring SSL is a bit trickier, but assuming you already have `mod_ssl` 
installed and your working directory is the project root:

    sudo a2enmod ssl
    sudo cp apache/mitCAclient.pem /etc/ssl/certs/
    cd /etc/apache2/sites-enabled
    sudo ln -s ../sites-available/default-ssl 000-default-ssl 

The fabfile should take care of the rest, in theory.
