#!/bin/bash

source activate rigbi-env

scenarios=`python /projects/open-rigbi/parallel/scenario_generator.py`

echo $scenarios

parallel --sshloginfile /projects/open-rigbi/parallel/nodelist -n1 --no-notice --progress /projects/open-rigbi/parallel/collect_scenario.sh ::: $scenarios

echo $complete
