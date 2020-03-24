#!/bin/bash -e

USAGE="$0 <SPLIT_PATH> <SOLVE_PATH> <MERGE_PATH> <CNF_PATH> <NUM_DIVIDES> <MARCH_PATH> <LINGELING_PATH>"

SPLIT_PATH=${1?$USAGE}
SOLVE_PATH=${2?$USAGE}
MERGE_PATH=${3?$USAGE}
CNF_PATH=${4?$USAGE}
NUM_DIVIDES=${5?$USAGE}
MARCH_PATH=${6?$USAGE}
LINGELING_PATH=${7?$USAGE}

SPLIT_HASH=$(gg-hash $SPLIT_PATH)
SOLVE_HASH=$(gg-hash $SOLVE_PATH)
MERGE_HASH=$(gg-hash $MERGE_PATH)
CNF_HASH=$(gg-hash $CNF_PATH)
MARCH_HASH=$(gg-hash $MARCH_PATH)
LINGELING_HASH=$(gg-hash $LINGELING_PATH)

rm -rf .gg

gg-init

gg-collect $SPLIT_PATH $SOLVE_PATH $MERGE_PATH $CNF_PATH $MARCH_PATH $LINGELING_PATH

function placeholder() {
    echo "@{GGHASH:$1}"
}

SPLIT_OUT_PREFIX="splitOut"

gg-create-thunk \
    --executable $MARCH_HASH \
    --executable $SPLIT_HASH \
    $(for i in $(seq 0 $((2 ** $NUM_DIVIDES - 1))); do echo --output "$SPLIT_OUT_PREFIX.$i"; done) \
    --placeholder split.thunk \
    --value $CNF_HASH \
    -- \
    $SPLIT_HASH splitter.py \
    $(placeholder $MARCH_HASH) \
    $(placeholder $CNF_HASH) \
    $NUM_DIVIDES \
    $SPLIT_OUT_PREFIX
