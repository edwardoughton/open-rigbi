#!/bin/bash

source activate rigbi-env

countries=`python /projects/open-rigbi/parallel/country_generator.py`

echo $countries

parallel --sshloginfile /projects/open-rigbi/parallel/nodelist -n1 --no-notice --progress /projects/open-rigbi/parallel/run_preprocess_country.sh ::: $countries

echo $complete
