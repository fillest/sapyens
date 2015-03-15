#!/usr/bin/env bash

set -e
#set -x


if [ "$#" -ne 1 ]
then
	echo "usage error: provide project name as an argument"
	exit 1
fi
name="$1"


pcreate -t sapyens $name
mv $name ${name}__tmp
mv ${name}__tmp/* .
rmdir ${name}__tmp

chmod +x run
mv _.gitignore .gitignore
cp development.ini.example development.ini

pip install -e .

echo -e "\033[32mOK\033[0m"
