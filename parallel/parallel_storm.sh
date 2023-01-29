#!/bin/bash

source activate rigbi-env

scenarios=`python /projects/open-rigbi/parallel/storm_scenario_generator.py`

echo $scenarios

parallel --sshloginfile /projects/open-rigbi/parallel/nodelist -n1 --no-notice --progress /projects/open-rigbi/parallel/parallel_storm_country.sh ::: $scenarios

echo $complete
