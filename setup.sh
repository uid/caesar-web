#!/bin/sh

CAESAR_DIR=/var/django/caesar

# Set time zone.
#    **** comment out for now, not sure Caesar needs this
#echo America/New_York > /etc/timezone
#/usr/sbin/dpkg-reconfigure tzdata

# Install Linux packages we need.
apt-get update
apt-get install -y apache2 apache2-dev libldap2-dev libsasl2-dev git libapache2-mod-wsgi openjdk-7-jre python-dev python-numpy python-psycopg2 python-pip

# Install Python packages we need.
cd /tmp
pip install -r $CAESAR_DIR/requirements.txt

# Set permissions on Caesar folder tree
chgrp -R www-data $CAESAR_DIR/media
chmod -R g+ws $CAESAR_DIR/media

# Set up SSL, with MIT certificate authority for checking certificates presented by users.
cp $CAESAR_DIR/apache/mitCAclient.pem /etc/ssl/certs/
ln -sf /etc/apache2/sites-available/default-ssl /etc/apache2/sites-enabled/000-default-ssl 
a2enmod ssl

# Install Caesar into Apache
ln -sf $CAESAR_DIR/apache/caesar /etc/apache2/sites-available
a2ensite caesar

# Start or restart Apache
apachectl graceful
