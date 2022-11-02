#!/bin/bash
# . /etc/profile.d/profile.sh

# full_code=$1

# iso3=${full_code:0:3}

echo -----running on `hostname`: $1

DIR=/projects/open-rigbi

source activate rigbi-env

# mkdir -p $DIR/data/processed/$iso3/logs

# touch $DIR/data/processed/$iso3/logs/$1.txt

# python D:/github/open-rigbi/parallel/input_generator.py $1
# # D:\Github\open-rigbi\parallel\input_generator.py
# echo python `pwd`/parallel/sites.py
python $DIR/scripts/collect.py $1 #&> $DIR/data/processed/$iso3/logs/$1.txt

echo --completed: $1
