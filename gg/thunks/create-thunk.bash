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

gg-collect $SPLIT_PATH $SOLVE_PATH $MERGE_PATH $CNF_PATH $MARCH_PATH $LINGELING_PATH > /dev/null

function placeholder() {
    echo "@{GGHASH:$1}"
}

function outputPlaceholder(){
    echo "@{GGHASH:$1#$2}"
}

SPLIT_OUT_PREFIX="splitOut"

splitThunkHash=$( { gg-create-thunk \
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
                  } 2>&1 )

SOLVER_OUT_PREFIX="solverOut"
for i in $(seq 0 $((2 ** $NUM_DIVIDES - 1)))
do
    # GG doesn't allow you to refer to the first output of any thunk by name,
    # so we have to special case the first output. Frickin ridiculous...
    if [[ $i == "0" ]]
    then
        p=$(placeholder $splitThunkHash)
    else
        p=$(outputPlaceholder $splitThunkHash "$SPLIT_OUT_PREFIX.$i")
    fi
    gg-create-thunk \
        --executable $LINGELING_HASH \
        --executable $SOLVE_HASH \
        --output "$SOLVER_OUT_PREFIX.$i" \
        --placeholder solve$i.thunk \
        --value $CNF_HASH \
        --thunk $splitThunkHash \
        -- \
        $SOLVE_HASH solve.py \
        $(placeholder $LINGELING_HASH) \
        $(placeholder $CNF_HASH) \
        $p \
        $SOLVER_OUT_PREFIX.$i 2>&1
done
