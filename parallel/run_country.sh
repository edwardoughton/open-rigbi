#!/bin/bash
# . /etc/profile.d/profile.sh
echo $1: Running on `hostname`

# DIR=/projects/open-rigbi
DIR=$(pwd)

# echo $DIR

source activate rigbi-env
#cd D:/github/open-rigbi/
cd $DIR

#cd /soge-home/projects/mistral/nismod/digital_comms
#mkdir -p D:/github/open-rigbi/data/test/$1
mkdir -p $DIR/data/processed/$1

#touch D:/github/open-rigbi/data/test/$1/log.txt
touch $DIR/data/processed/$1/log.txt

# python D:/github/open-rigbi/parallel/input_generator.py $1
# # D:\Github\open-rigbi\parallel\input_generator.py
# echo python `pwd`/parallel/sites.py
python $DIR/scripts/process.py $1 &> $DIR/data/processed/$1/log.txt
