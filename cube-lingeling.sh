#!/usr/bin/env bash
set -x
DIR=/tmp
CNC_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
USAGE="$0 CNF N_WORKERS [TEMP_DIR]"
CNF=${1?$USAGE}
PAR=${2?$USAGE}
TEMP_DIR=$3
TEMP_DIR=${TEMP_DIR:-/tmp}
$CNC_DIR/march_cu/march_cu $CNF -o $DIR/cubes$$ $4 $5 $6 $7 $8 $9
echo "p inccnf" > $DIR/formula$$.icnf
cat $CNF | grep -v c >> $DIR/formula$$.icnf
cat $DIR/cubes$$ >> $DIR/formula$$.icnf
(time $CNC_DIR/lingeling/ilingeling $DIR/formula$$.icnf $PAR)
rm $DIR/formula$$.icnf
