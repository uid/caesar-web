# Update packages list before attempting to install any
exec {
  'apt-get update':
    command => '/usr/bin/apt-get update';
}
Exec['apt-get update'] -> Package <| |>

# Install packages
package {
  [ 'apache2', 'apache2-dev', 'libldap2-dev', 'libsasl2-dev', 'git', 'libapache2-mod-wsgi', 'python-numpy', 'python-psycopg2', 'postfix' ]:
    ensure => 'installed';
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
