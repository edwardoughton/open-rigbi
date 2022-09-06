#!/bin/bash

countries=`python /projects/open-rigbi/parallel/input_generator.py`

echo $countries

#seq 1 $count | parallel -n1 --no-notice ./plot_stations.py {}
parallel --sshloginfile /projects/open-rigbi/parallel/nodelist -n1 --no-notice --progress /projects/open-rigbi/parallel/run_country.sh ::: $countries

echo 'parallel processing complete'
