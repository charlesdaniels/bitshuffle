#!/bin/bash
./setup.py sdist
./setup.py bdist_wheel
printf 'Upload project to PyPI? [no]: '
read -r confirm
if [[ $confirm = y* ]] ; then twine upload dist/*; fi

