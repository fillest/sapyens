from fabric.api import local, task, env, put, hosts, parallel
from fabric.context_managers import lcd, prefix, settings, cd
from glob import glob
from os.path import basename, exists


class Error (Exception):
	pass


if not env.get('proj_name'):
	raise Error("provide env.proj_name")

# env.linewise = True #for parallel execution

local_deploy_tmp_path = '/tmp/%s/deploy' % env.proj_name
remote_tmp_path = '/tmp/%s' % env.proj_name
remote_deploy_tmp_path = remote_tmp_path + '/deploy'
remote_app_path = '/opt/%s' % env.proj_name
remote_venv_activate = 'source %s/venv/bin/activate' % remote_app_path

# def build_path ():
# 	return '/tmp/%s/build' % env.proj_name

# def remote_dist_path ():
# 	return '/tmp/{build_path}/{build_path}_dist.tar.gz'.format(build_path = build_path())

# @task
# @hosts('')
# def build():
# 	"""build sdist"""
# 	# local('cp -r . ' + build_path())
# 	local('rsync --archive . {build_path} --exclude venv --exclude ".git" --exclude "*.egg-info" --exclude "*.pyc"'.format(build_path = build_path()))
# 	# local('rm -r {build_path}/*.egg-info'.format(build_path = build_path()))
# 	with lcd(build_path()):
# 		local('python setup.py --quiet sdist')

# @task
# @parallel
# def upload_sdist ():
# 	local_path, remote_path = tarball_upload_paths(build_path() + '/dist')
# 	put(local_path, remote_path)

def tarball_upload_paths (parent_path):
	local_path = glob(parent_path + '/*.tar.gz')[0]
	fname = basename(local_path)
	remote_path = '%s/%s' % (remote_deploy_tmp_path, fname)
	return local_path, remote_path