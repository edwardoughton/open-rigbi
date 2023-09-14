#!/bin/bash
# . /etc/profile.d/profile.sh

full_code=$1

echo -----running on `hostname`: full_code

iso3=${full_code:0:3}

DIR=/projects/open-rigbi

source activate rigbi-env

mkdir -p $DIR/data/processed/$iso3/logs

touch $DIR/data/processed/$iso3/logs/$iso3.txt

python $DIR/scripts/process.py $1 &> $DIR/data/processed/$iso3/logs/$1.txt

echo --completed: $1
