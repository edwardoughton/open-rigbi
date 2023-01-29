#!/bin/bash
# . /etc/profile.d/profile.sh

echo -----running on `hostname`: $1

DIR=/projects/open-rigbi

source activate rigbi-env

#mkdir -p $DIR/data/processed/results/logs
#touch $DIR/data/processed/results/logs/$1.txt

# # D:\Github\open-rigbi\parallel\input_generator.py
# echo python `pwd`/parallel/sites.py
python $DIR/scripts/tropical_storms.py $1 #&> $DIR/data/processed/results/logs/$1.txt

echo --completed: $1
