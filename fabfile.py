from fabric.api import *

env.project_name = 'caesar'

def prod():
    env.hosts = ['caesar.xvm.mit.edu']
    env.path = '/var/django/caesar'

def deploy():
    """
    Pulls the latest code from git and deploys it.
    """
    update_code()
    install_project()
    restart_webserver()

def update_code():
    with cd(env.path):
        run('git pull')

def install_project():
    # symlink the caesar apache configuration file to apache
    sudo('cd /etc/apache2/sites-enabled; ln -sf %(path)s/apache/%(project_name)s %(project_name)s' % env)
    with cd(env.path):
        run('python manage.py collectstatic --noinput')
        run('python manage.py syncdb --noinput')
        run('python manage.py migrate')

def restart_webserver():
    sudo('service apache2 restart')

