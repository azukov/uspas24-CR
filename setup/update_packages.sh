#!/bin/bash
HERE="$( dirname "${BASH_SOURCE[0]}" )"

OLD=$(pwd)

cd $HERE
git pull
python environment.py --packages ../env
cd $OLD

