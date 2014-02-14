#!/bin/sh

CAESAR_DIR=/var/django/caesar

# Set time zone.
#    **** comment out for now, not sure Caesar needs this
#echo America/New_York > /etc/timezone
#/usr/sbin/dpkg-reconfigure tzdata

# Install Linux packages we need.
/usr/bin/apt-get update
/usr/bin/apt-get install -y apache2 apache2-dev libldap2-dev libsasl2-dev git libapache2-mod-wsgi openjdk-7-jre python-dev python-numpy python-psycopg2 python-pip postfix 

# Install Python packages we need.
cd /tmp
pip install -r $CAESAR_DIR/requirements.txt

# Make caesar user and group accounts.
useradd -r caesar
adduser caesar www-data
adduser vagrant www-data

# Make the media folder
mkdir $CAESAR_DIR/media

# Set permissions on Caesar folder tree so that Apache server can write to the database and media folder.
chgrp -R www-data $CAESAR_DIR/fixtures $CAESAR_DIR/media

# Set up SSL, with MIT certificate authority for checking certificates presented by users.
cp $CAESAR_DIR/apache/mitCAclient.pem /etc/ssl/certs/
ln -sf /etc/apache2/sites-available/default-ssl /etc/apache2/sites-enabled/000-default-ssl 
a2enmod ssl

# Install Caesar into Apache and start or restart Apache.
ln -sf $CAESAR_DIR/apache/caesar /etc/apache2/sites-available
a2ensite caesar
sudo /etc/init.d/apache2 restart
