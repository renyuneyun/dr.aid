#!/usr/bin/env zsh

dir_name=${PWD##*/}

# Type check using mypy

cd .. && mypy --config-file=$dir_name/.mypy.ini $dir_name/*.py $dir_name/draid/*.py &&

echo "mypy with no errors" &&

# Unit test

cd $dir_name && pytest tests &&

# Pylint

cd .. &&

pylint --rcfile=$dir_name/.pylintrc_high $dir_name/main.py $dir_name/draid $dir_name/draid/proto &&

pylint --rcfile=$dir_name/.pylintrc $dir_name/main.py $dir_name/draid $dir_name/draid/proto

