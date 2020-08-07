#!/bin/bash

export PYTHONPATH=/barrett/scratch/haozewu/gg-parallelization/gg/tools/pygg/:$PYTHONPATH
PATH=/barrett/scratch/haozewu/gg-parallelization/CnC/gg/frontend:$PATH

source /barrett/scratch/haozewu/gg-parallelization/py37/bin/activate

python3.7 /barrett/scratch/haozewu/gg-parallelization/CnC/gg/runner.py "$@"

deactivate


