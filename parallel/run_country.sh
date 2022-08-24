
#!/bin/bash
# . /etc/profile.d/profile.sh
echo $1: Running on `hostname`

source activate rigbi-env
cd D:/github/open-rigbi/

#cd /soge-home/projects/mistral/nismod/digital_comms
mkdir -p D:/github/open-rigbi/data/test/$1
touch D:/github/open-rigbi/data/test/$1/log.txt

# python D:/github/open-rigbi/parallel/input_generator.py $1
# # D:\Github\open-rigbi\parallel\input_generator.py
# echo python `pwd`/parallel/sites.py
python `pwd`/parallel/sites.py $1 &> D:/github/open-rigbi/data/test/$1/log.txt
