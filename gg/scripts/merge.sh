#!/bin/bash -e

numDivides=$1
output=$2

shift 2

n=$( { for f in $@; do cat $f | grep -o "UNSAT" | uniq; done } | wc -l)
if [[ $n == $# ]]
then
    echo "UNSAT" > $output
else
    echo "SAT" > $output
fi
