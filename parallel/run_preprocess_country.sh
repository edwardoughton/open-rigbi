#!/bin/bash
# . /etc/profile.d/profile.sh

echo -----running on `hostname`: $1

DIR=/projects/open-rigbi

source activate rigbi-env

mkdir -p $DIR/data/processed/$1/logs

touch $DIR/data/processed/$1/logs/$1.txt

python $DIR/scripts/preprocess.py $1 &> $DIR/data/processed/$1/logs/$1.txt

echo --completed: $1
