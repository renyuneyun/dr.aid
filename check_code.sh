#!/usr/bin/env zsh

dir_name=${PWD##*/}
cd ..

mypy --config-file=$dir_name/.mypy.ini $dir_name/*.py &&

echo "mypy with no errors" &&

pylint --rcfile=$dir_name/.pylintrc $dir_name

