#!/bin/bash
./setup.py sdist
./setup.py bdist_wheel
printf 'Upload project to PyPI? [no]: '
read -r confirm
if $(echo "$confirm" | grep '^y.*') ; then twine upload dist/*; fi

