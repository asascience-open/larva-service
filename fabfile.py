from fabric.api import *

env.user = "larva"
env.key_filename = '/home/dev/.ssh/particles.key'

code_dir = "/home/larva/larva-service"

env.roledefs.update({
    'web': [],
    'datasets': [],
    'runs': ["ec2-50-16-124-101.compute-1.amazonaws.com"],
    'all' : ['174.129.241.244']
})

def admin():
    env.user = "ec2-user"
def larva():
    env.user = "larva"

@roles('runs')
def deploy_runs(paegan=None):
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs(paegan)
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start runs")

@roles('datasets')
def deploy_datasets(paegan=None):
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs(paegan)
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start datasets")

@roles('web')
def deploy_web(paegan=None):
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs(paegan)
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start gunicorn")

@roles('all')
def deploy_all(paegan=None):
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs(paegan)
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start all")

def update_paegan():
    larva()
    with cd(code_dir):
        run("pip uninstall -y paegan paegan-viz")
        with settings(warn_only=True):
            run("rm -rf ~/.virtualenvs/larva/build/paegan")
            run("rm -rf ~/.virtualenvs/larva/build/paegan-viz")
        run("pip install --upgrade --no-deps git+https://github.com/asascience-open/paegan.git@master#egg=paegan")
        run("pip install --upgrade --no-deps git+https://github.com/asascience-open/paegan-viz.git@master#egg=paegan-viz")

def update_libs(paegan=None):
    larva()
    with cd(code_dir):
        with settings(warn_only=True):
            if paegan:
                update_paegan()
            run("pip install -r requirements.txt")

@roles('web', 'all')
def restart_nginx():
    admin()
    run("sudo /etc/init.d/nginx restart")

@roles('runs','datasets','web','all')
def supervisord_restart():
    stop_supervisord()
    start_supervisord()

def stop_supervisord():
    larva()
    with cd(code_dir):
        with settings(warn_only=True):
            run("supervisorctl -c ~/supervisord.conf stop all")
            run("kill -QUIT $(ps aux | grep supervisord | grep -v grep | awk '{print $2}')")

    kill_pythons()

def kill_pythons():
    admin()
    with settings(warn_only=True):
        run("sudo kill -QUIT $(ps aux | grep python | grep -v supervisord | awk '{print $2}')")

def start_supervisord():
    larva()
    with cd(code_dir):
        with settings(warn_only=True):    
            run("supervisord -c ~/supervisord.conf")

@roles('runs','datasets','web','all')
def upload_key_to_larva():
    admin()
    with settings(warn_only=True):
        run("sudo su -c \"echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCDBacNAOzKzPmFpJOClNrUwAsoh9YCzpKKqenbbbXQ/fqDVsOw/z522YDYuGoiZ6475YBET9L13ck4xh0XP5rykUvnAs0pvW7Vu1ttPxHx2wDmTfffRtN9Zbw4Y19c9vy9+NeIjrJxyLWwwnBrPHqf1R+O9HuvgmVSccevVnGpaaOJ9puaAFrmNO5cXxEI4WW+6+jsMBaVZqIaOl4U/eMcPTOsP8fn7+ME0YuIAIM2QDZMAUlWablhFYmkP8yfHIehc6IKgV0SupPOjH4vNTeJTMB0uPxhXDuwlJaW2zmxf+hbz7fR4X+WTgryBdUbksdCUuyTkDyERHUiwL8JbsQZ asa-particles-ec2' > /home/larva/.ssh/authorized_keys\"")
        run("sudo chown larva:larva /home/larva/.ssh/authorized_keys")
        run("sudo chmod 600 /home/larva/.ssh/authorized_keys")
        run("sudo chmod 700 /home/larva/.ssh")

@roles('runs','datasets','web','all')
def setup_filesystem():
    admin()
    with settings(warn_only=True):
        run("sudo mount /dev/sdb /data")
        run("sudo umount /dev/sdc")
        run("sudo mount /dev/sdc /scratch")
        run("sudo mkdir /scratch/output")
        run("sudo mkdir /scratch/cache")
        run("sudo chown -R larva:larva /scratch")
        run("sudo chown -R larva:larva /data")
