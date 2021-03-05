#!/bin/bash

export PYTHONPATH=/homes/haozewu/CnC/gg/gg/tools/pygg/:$PYTHONPATH
PATH=/homes/haozewu/CnC/gg/frontend:$PATH

source /homes/haozewu/py3.6/bin/activate

python /homes/haozewu/CnC/gg/runner.py "$@"

deactivate
