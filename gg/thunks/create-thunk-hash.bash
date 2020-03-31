#!/bin/bash -e

USAGE="$0 <SPLIT_HASH> <SOLVE_HASH> <MERGE_HASH> <CNF_HASH> <NUM_DIVIDES> <TIMEOUT> <TIMEOUT_FACTOR> <MARCH_HASH> <LINGELING_HASH> <GG_INIT_HASH> <GG_HASH_HASH> <GG_CREATE_THUNK_HASH>"


SPLIT_HASH=${1?$USAGE}
SOLVE_HASH=${2?$USAGE}
MERGE_HASH=${3?$USAGE}
CNF_HASH=${4?$USAGE}
NUM_DIVIDES=${5?$USAGE}
TIMEOUT=${6?$USAGE}
TIMEOUT_FACTOR=${7?$USAGE}
MARCH_HASH=${8?$USAGE}
LINGELING_HASH=${9?$USAGE}
GG_INIT_HASH=${10?$GG_INIT_HASH}
GG_HASH_HASH=${11?$GG_HASH_HASH}
GG_CREATE_THUNK_HASH=${12?$GG_CREATE_THUNK_HASH}
SELF_HASH=$(gg-hash $(readlink -f $0))

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
                        --value $CNF_HASH \
                        -- \
                        $SPLIT_HASH splitter.py \
                        $(placeholder $MARCH_HASH) \
                        $(placeholder $CNF_HASH) \
                        $NUM_DIVIDES \
                        $SPLIT_OUT_PREFIX
                  } 2>&1 )

SOLVER_OUT_PREFIX="solverOut"
solverHashes=$(for i in $(seq 0 $((2 ** $NUM_DIVIDES - 1)))
do
    echo "Solver $i" >&2
    # GG doesn't allow you to refer to the first output of any thunk by name,
    # so we have to special case the first output. Frickin ridiculous...
    if [[ $i == "0" ]]
    then
        h="$splitThunkHash"
        p=$(placeholder $splitThunkHash)
    else
        h="$splitThunkHash#$SPLIT_OUT_PREFIX.$i"
        p=$(outputPlaceholder $splitThunkHash "$SPLIT_OUT_PREFIX.$i")
    fi
    gg-create-thunk \
        --executable $LINGELING_HASH \
        --executable $SOLVE_HASH \
        --executable $GG_INIT_HASH \
        --executable $GG_HASH_HASH \
        --executable $GG_CREATE_THUNK_HASH \
        --executable $SELF_HASH \
        --output "$SOLVER_OUT_PREFIX.$i" \
        --value $CNF_HASH \
        --thunk $h \
        -- \
        $SOLVE_HASH solve.py \
        $(placeholder $LINGELING_HASH) \
        $(placeholder $CNF_HASH) \
        $p \
        $SOLVER_OUT_PREFIX.$i \
        $(placeholder $GG_INIT_HASH) \
        $(placeholder $GG_HASH_HASH) \
        $(placeholder $GG_CREATE_THUNK_HASH) \
        $(placeholder $SELF_HASH) \
        $MARCH_HASH \
        $NUM_DIVIDES \
        $TIMEOUT \
        $TIMEOUT_FACTOR \
        $SOLVE_HASH \
        $SPLIT_HASH \
        $MERGE_HASH \
        2>&1
done
)
echo "Solver hashes: $solverHashes"

gg-create-thunk \
    --executable $MERGE_HASH \
    --output out \
    $(for h in $solverHashes; do echo --thunk $h; done) \
    --placeholder output.thunk \
    -- \
    $MERGE_HASH merge.py \
    $NUM_DIVIDES \
    out \
    $(for h in $solverHashes; do echo $(placeholder $h); done)
