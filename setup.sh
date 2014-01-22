#!/bin/sh

# Set time zone.
#    **** comment out for now, not sure Caesar needs this
#echo America/New_York > /etc/timezone
#/usr/sbin/dpkg-reconfigure tzdata

# Install Linux packages we need.
/usr/bin/apt-get update
/usr/bin/apt-get install -y apache2 apache2-dev libldap2-dev libsasl2-dev git libapache2-mod-wsgi python-dev python-numpy python-psycopg2 python-pip postfix 

# Install Python packages we need.
cd /var/django/caesar
pip install -r requirements.txt

# Make caesar user and group accounts.
useradd -r caesar
groupadd dev
adduser caesar dev
adduser vagrant dev
adduser www-data dev

# Set permissions on Caesar folder tree.
#    **** hmm, chmod/chgrp/chown have no effect on the synced folder, so skip this for now 
# cd /var/django/caesar
# chgrp -R dev .
# chown -R $USER .
# chmod -R g+w .
# chmod -R g+s .

# Make the media folder
cd /var/django/caesar
mkdir media && chmod g+w media

# Set up SSL, with MIT certificate authority for checking certificates presented by users.
cp /var/django/caesar/apache/mitCAclient.pem /etc/ssl/certs/
cd /etc/apache2/sites-enabled
ln -s ../sites-available/default-ssl 000-default-ssl 
a2enmod ssl

# Install Caesar into Apache and start or restart Apache.
ln -sf /var/django/caesar/apache/caesar /etc/apache2/sites-available
a2ensite caesar
sudo /etc/init.d/apache2 restart

