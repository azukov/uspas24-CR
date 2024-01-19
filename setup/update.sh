#!/bin/bash
HERE="$( dirname "${BASH_SOURCE[0]}" )"

OLD=$(pwd)

cd $HERE
git pull
cd $OLD

