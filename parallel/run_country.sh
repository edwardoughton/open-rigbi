#!/bin/bash
# . /etc/profile.d/profile.sh
echo -----running on `hostname`: $1

DIR=/projects/open-rigbi

source activate rigbi-env

mkdir -p $DIR/data/processed/$1

touch $DIR/data/processed/$1/log.txt

# python D:/github/open-rigbi/parallel/input_generator.py $1
# # D:\Github\open-rigbi\parallel\input_generator.py
# echo python `pwd`/parallel/sites.py
python $DIR/scripts/process.py $1 &> $DIR/data/processed/$1/log.txt

echo --completed: $1
