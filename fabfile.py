from fabric.api import *
from fabric.contrib.files import *
import os
from copy import copy
import time

"""
    Call this with fab -c .fab TASK to pick up deploy variables
    Required variables in .fab file:
        webpass = x
        secret_key = x
        mongo_db = x
        redis_db = x
        aws_access = x
        aws_secret = x
        key_filename = x
"""

env.user = "larva"

code_dir = "/home/larva/larva-service"

data_snapshot = "snap-94f3cfd7"

env.roledefs.update({
    'setup'     : ['ec2-50-16-20-142.compute-1.amazonaws.com'],
    'web'       : ['services.larvamap.asascience.com'],
    'datasets'  : [],
    'shorelines': [],
    'runs'      : [],
    'workers'   : [],
    'all'       : []
})
# For copy and pasting when running tasks system wide
# @roles('web','datasets','shorelines','runs','workers','all')

def admin():
    env.user = "ec2-user"
def larva():
    env.user = "larva"

@roles('workers')
@parallel
def deploy_workers():
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs()
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start runs")
        run("supervisorctl -c ~/supervisord.conf start datasets")
        run("supervisorctl -c ~/supervisord.conf start shorelines")

@roles('runs')
@parallel
def deploy_runs():
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs()
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start runs")

@roles('datasets')
@parallel
def deploy_datasets():
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs()
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start datasets")

@roles('shorelines')
@parallel
def deploy_shorelines():
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs()
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start shorelines")

@roles('web')
@parallel
def deploy_web():
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs()
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start gunicorn")

@roles('all')
@parallel
def deploy_all():
    stop_supervisord()

    larva()
    with cd(code_dir):
        run("git pull origin master")
        update_libs()
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start all")

@roles('setup')
@parallel
def setup():
    # Based on Amazon Linux AMI
    admin()

    # Enable EPEL repo
    put(local_path='deploy/epel.repo', remote_path='/etc/yum.repos.d/epel.repo', use_sudo=True, mirror_local_mode=True)

    # Install additonal packages
    sudo("yum -y install proj-devel geos-devel git nginx python27 python27-devel gcc gcc-c++ make freetype-devel libpng-devel libtiff-devel libjpeg-devel")

    # Add /usr/local/lib to ld's path
    setup_ld()

    # Setup larva user
    setup_larva_user()

    # Setup the python virtualenv
    setup_burrito()

    # Install GDAL
    setup_gdal()

    # Get code
    setup_code()

    # Setup Nginx
    setup_nginx()

    # Data/Bathy
    setup_data()

    # Setup Filesystem
    setup_filesystem()

    # Setup a Munin node
    setup_munin()

    # Setup supervisord
    update_supervisord()

def setup_ld():
    admin()
    sudo("su -c \"echo '/usr/local/lib' > /etc/ld.so.conf.d/local.conf\"")
    sudo("ldconfig")

def setup_gdal():
    admin()
    run("cd ~")
    run("wget http://download.osgeo.org/gdal/gdal-1.9.2.tar.gz")
    run("tar zxvf gdal-1.9.2.tar.gz")
    with cd("gdal-1.9.2"):
        run("./configure; make -j 4")
        sudo("make install")

def setup_nginx():
    admin()
    put(local_path='deploy/nginx.conf', remote_path='/etc/nginx/nginx.conf', use_sudo=True, mirror_local_mode=True)
    upload_template('deploy/nginx_larva.conf', '/etc/nginx/conf.d/larva.conf', context=copy(env), use_jinja=True, use_sudo=True, backup=False, mirror_local_mode=True)
    sudo("chkconfig nginx on")
    restart_nginx()

def update_supervisord():
    larva()
    run("pip install supervisor")
    upload_template('deploy/supervisord.conf', '/home/larva/supervisord.conf', context=copy(env), use_jinja=True, use_sudo=False, backup=False, mirror_local_mode=True, template_dir='.')

def setup_code():
    larva()
    with cd("~"):
        run("rm -rf larva-service")
        run("git clone https://github.com/asascience-open/larva-service.git")

    update_netcdf_libraries()

@roles('runs','datasets','shorelines','web','all')
def update_netcdf_libraries():
    admin()
    run("cd ~")
    run("wget https://asa-dev.s3.amazonaws.com/installNCO.txt")
    run("chmod 744 installNCO.txt")
    sudo("./installNCO.txt")

    larva()
    with cd(code_dir):
        with settings(warn_only=True):
            run("pip uninstall netCDF4 numpy")

        run("pip install numpy==1.6.2")
        run("HDF5_DIR=/usr/local/hdf5-1.8.10-patch1 NETCDF4_DIR=/usr/local/netcdf-4.2.1.1 PATH=$PATH:/usr/local/bin pip install -r requirements.txt")

def setup_burrito():
    larva()
    run("curl -s https://raw.github.com/brainsik/virtualenv-burrito/master/virtualenv-burrito.sh | $SHELL")
    run("mkvirtualenv -p /usr/bin/python27 larva")
    run("echo 'workon larva' >> ~/.bash_profile")

def setup_larva_user():
    admin()
    # Setup larva user
    sudo("useradd larva")
    sudo("mkdir /home/larva/.ssh")
    upload_key_to_larva()
    sudo("chown -R larva:larva /home/larva/.ssh")

def update_libs():
    larva()
    with cd(code_dir):
        with settings(warn_only=True):
            run("pip uninstall -y paegan paegan-viz paegan-transport")
            run("pip install -r requirements.txt")

def restart_nginx():
    admin()
    sudo("/etc/init.d/nginx restart")

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
        sudo("kill -QUIT $(ps aux | grep python | grep -v supervisord | awk '{print $2}')")

def start_supervisord():
    larva()
    with cd(code_dir):
        with settings(warn_only=True):
            run("supervisord -c ~/supervisord.conf")

def upload_key_to_larva():
    admin()
    with settings(warn_only=True):
        sudo("su -c \"echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCDBacNAOzKzPmFpJOClNrUwAsoh9YCzpKKqenbbbXQ/fqDVsOw/z522YDYuGoiZ6475YBET9L13ck4xh0XP5rykUvnAs0pvW7Vu1ttPxHx2wDmTfffRtN9Zbw4Y19c9vy9+NeIjrJxyLWwwnBrPHqf1R+O9HuvgmVSccevVnGpaaOJ9puaAFrmNO5cXxEI4WW+6+jsMBaVZqIaOl4U/eMcPTOsP8fn7+ME0YuIAIM2QDZMAUlWablhFYmkP8yfHIehc6IKgV0SupPOjH4vNTeJTMB0uPxhXDuwlJaW2zmxf+hbz7fR4X+WTgryBdUbksdCUuyTkDyERHUiwL8JbsQZ asa-particles-ec2' > /home/larva/.ssh/authorized_keys\"")
        sudo("chmod 600 /home/larva/.ssh/authorized_keys")
        sudo("chmod 700 /home/larva/.ssh")

@roles('setup')
def setup_data():
    admin()
    with settings(warn_only=True):
        sudo("umount /data")
        sudo("umount /dev/sdf")
        sudo("mkdir /data")

    # Get instance's ID
    instance_id = run("wget -q -O - http://169.254.169.254/latest/meta-data/instance-id")
    # Get instance's availability zone
    zone = run("wget -q -O - http://169.254.169.254/latest/meta-data/placement/availability-zone")

    # Detach the current volume
    detach_vol_id = run("ec2-describe-instances %s --aws-access-key %s --aws-secret-key %s | awk '/\/dev\/sdf/ {print $3}'" % (instance_id, env.aws_access, env.aws_secret))
    if detach_vol_id.find("vol-") == 0:
        run("ec2-detach-volume %s --aws-access-key %s --aws-secret-key %s" % (detach_vol_id, env.aws_access, env.aws_secret))

    # Create new volume from snapshot
    volume = run("ec2-create-volume --aws-access-key %s --aws-secret-key %s --snapshot %s -z %s" % (env.aws_access, env.aws_secret, data_snapshot, zone))
    #volume = "VOLUME    vol-164df04f    20  snap-94f3cfd7   us-east-1c  creating    2013-04-17T19:40:05+0000    standard"
    vol_index = volume.find("vol-")
    volume_id = volume[vol_index:vol_index+12]

    # Wait for the old volume to be detached and new volume to be created
    time.sleep(30)
    sudo("ec2-attach-volume --aws-access-key %s --aws-secret-key %s -d /dev/sdf -i %s %s" % (env.aws_access, env.aws_secret, instance_id, volume_id))

    # Delete the old volume
    if detach_vol_id.find("vol-") == 0:
        run("ec2-delete-volume %s --aws-access-key %s --aws-secret-key %s" % (detach_vol_id, env.aws_access, env.aws_secret))

@roles('setup')
def setup_filesystem():
    admin()
    with settings(warn_only=True):
        # Data is mounted at /dev/sdf
        sudo("mount /dev/sdf /data")
        sudo("chown -R larva:larva /data")

        # Use /dev/sdb because it is the only one a small instance will have
        sudo("umount /media/ephemeral*")
        sudo("umount /dev/sdb")
        sudo("umount /scratch")
        sudo("mkfs.ext4 /dev/sdb")
        sudo("mkdir /scratch")
        sudo("mount /dev/sdb /scratch")
        sudo("mkdir -p /scratch/output")
        sudo("mkdir -p /scratch/cache")
        sudo("chown -R larva:larva /scratch")

def setup_munin():
    admin()
    sudo("yum install -y munin-node")
    sudo("chkconfig munin-node on")
    run("echo \"allow ^107\.22\.197\.91$\" | sudo tee -a /etc/munin/munin-node.conf")
    run("echo \"allow ^10\.190\.178\.210$\" | sudo tee -a /etc/munin/munin-node.conf")
    sudo("/etc/init.d/munin-node restart")


# Usually this is all that needs to be called
def deploy():
    if env.roledefs['web']:
        execute(deploy_web)
    if env.roledefs['datasets']:
        execute(deploy_datasets)
    if env.roledefs['shorelines']:
        execute(deploy_shorelines)
    if env.roledefs['runs']:
        execute(deploy_runs)
    if env.roledefs['workers']:
        execute(deploy_workers)
    if env.roledefs['all']:
        execute(deploy_all)
