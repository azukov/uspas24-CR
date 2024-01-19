#!/bin/bash
HERE="$( dirname "${BASH_SOURCE[0]}" )"

OLD=$(pwd)

cd $HERE
echo "Recreating python virtual environment."
rm -rf ../env
python environment.py --new ../env
cd $OLD
echo Activate user environment with \"source \~/uspas24-CR/env/bin/activate\"

