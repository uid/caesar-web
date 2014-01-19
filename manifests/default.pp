# Update packages list before attempting to install any
exec {
  'apt-get update':
    command => '/usr/bin/apt-get update';
}
Exec['apt-get update'] -> Package <| |>

# Add archive for Node.js before attempting to install it
exec {
  'add-apt node':
    command => 'add-apt-repository ppa:chris-lea/node.js && apt-get update',
    path => [ '/usr/bin', '/bin' ],
    require => Package['python-software-properties'],
    creates => '/etc/apt/sources.list.d/chris-lea-node_js-precise.list';
}
Exec['add-apt node'] -> Package['nodejs']

# Install packages
package {
  [ 'vim', 'python-software-properties', 'git', 'make', 'nodejs' ]:
    ensure => 'installed';
}

exec {
  'get bootstrap':
    command => 'wget -q -O - http://bootswatch.com/2/superhero/bootstrap.min.css | sed "s/@import[^;]*;//" > bootstrap-superhero.min.css',
    path => [ '/bin', '/usr/bin' ],
    cwd => '/vagrant/public/bootstrap/css',
    creates => '/vagrant/public/bootstrap/css/bootstrap-superhero.min.css';
}

# Generate SSL certificate
exec {
  'ssl certificate':
    command => 'openssl genrsa -out ssl-private-key.pem 1024 && openssl req -new -key ssl-private-key.pem -config config/openssl.conf | openssl x509 -req -signkey ssl-private-key.pem -out ssl-certificate.pem',
    path => '/usr/bin',
    cwd => '/vagrant',
    creates => '/vagrant/ssl-certificate.pem';
  
  'ssl ca':
    command => 'wget -q -O - http://ca.mit.edu/mitClient.crt | openssl x509 -inform der -out ssl-ca.pem',
    path => '/usr/bin',
    cwd => '/vagrant',
    creates => '/vagrant/ssl-ca.pem';
}

# Set time zone
file {
  '/etc/timezone':
    content => "America/New_York\n";
}
exec {
  'reconfigure tzdata':
    command => '/usr/sbin/dpkg-reconfigure tzdata',
    subscribe => File['/etc/timezone'],
    require => File['/etc/timezone'],
    refreshonly => true;
}
