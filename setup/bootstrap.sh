#!/bin/bash
HERE="$( dirname "${BASH_SOURCE[0]}" )"
cp $HERE/pycharm.desktop $HOME/.local/share/applications

OLD=$(pwd)

cd $HERE
python -m venv ../env
source ../env/bin/activate
pip install -U pip
pip install numpy scipy matplotlib pcaspy pyepics
pip install PyORBIT-0.1.dev1199+g62416c4-cp310-cp310-linux_x86_64.whl
cd $OLD

