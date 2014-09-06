#!/usr/bin/env bash

set -e
#set -x


if [ "$#" -ne 1 ]
then
	echo "usage error: provide project name as an argument"
	exit 1
fi
name="$1"


mkdir $name
cd $name
virtualenv --no-site-packages venv
venv/bin/pip install -e ../sapyens/
venv/bin/pip install -r ../sapyens/requirements_project_fresh.txt
venv/bin/pcreate -t sapyens $name
mv $name ${name}__tmp
mv ${name}__tmp/* .
rmdir ${name}__tmp

chmod +x run
mv _.gitignore .gitignore
cp development.ini.example development.ini

venv/bin/pip install -e .

echo -e "\033[32mOK\033[0m"
