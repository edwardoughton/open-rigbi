#!/bin/bash
# source activate rigbi-env

countries=`python /projects/open-rigbi/parallel/input_generator.py`

echo $countries

# echo `pwd`/scripts/network_preprocess_input_files.sh $countries
#seq 1 $count | parallel -n1 --no-notice ./plot_stations.py {}
parallel --sshloginfile /projects/open-rigbi/parallel/nodelist -n1 --no-notice --progress /projects/open-rigbi/parallel/run_country.sh ::: $countries

echo 'parallel processing complete'
