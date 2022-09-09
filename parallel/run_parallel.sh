#!/bin/bash

countries=`python /projects/open-rigbi/parallel/input_generator.py`

echo $countries

parallel --sshloginfile /projects/open-rigbi/parallel/nodelist -n1 --no-notice --progress /projects/open-rigbi/parallel/run_country.sh ::: $countries

echo 'parallel processing complete'
