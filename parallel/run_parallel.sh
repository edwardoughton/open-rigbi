#!/bin/bash
countries=`python parallel/input_generator.py`

# echo $countries

echo `pwd`/scripts/network_preprocess_input_files.sh $countries

#seq 1 $count | parallel -n1 --no-notice ./plot_stations.py {}
parallel --sshloginfile nodeslist -n1 --no-notice --progress `pwd`/scripts/network_preprocess_input_files.sh ::: $countries

echo 'parallel processing complete'
