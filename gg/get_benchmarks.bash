#!/usr/bin/env bash

set -xe

UNZIP="unzip"
UN7ZIP="p7zip -d"

# https://stackoverflow.com/questions/59895/how-to-get-the-source-directory-of-a-bash-script-from-within-the-script-itself
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[[0]]}" )" >/dev/null 2>&1 && pwd )"

DOWNLOADS_DIR="$SCRIPT_DIR/downloads"
mkdir -p $DOWNLOADS_DIR
BENCHMARKS_DIR="$SCRIPT_DIR/benchmarks"
mkdir -p $BENCHMARKS_DIR
FAMILIES_DIR="$SCRIPT_DIR/families"
mkdir -p $FAMILIES_DIR

SAT09_URL="http://www.cril.univ-artois.fr/SAT09/bench/appli.7z"
SAT18_URL="http://sat2018.forsyte.tuwien.ac.at/benchmarks/Main.zip"

SAT09_ZIP="$DOWNLOADS_DIR/SAT09.7z"
SAT18_ZIP="$DOWNLOADS_DIR/SAT18.zip"

SAT09_UNZIP_TEST_FILE="$DOWNLOADS_DIR/SAT09"
SAT18_UNZIP_TEST_FILE="$DOWNLOADS_DIR/Chen"

# Download the zips, if needed
if [[ ! -a $SAT18_ZIP ]]
then
    wget -O $SAT18_ZIP $SAT18_URL
fi
if [[ ! -a $SAT09_ZIP ]]
then
    wget -O $SAT09_ZIP $SAT09_URL
fi

# Unzip them, if needed
if [[ ! -a $SAT09_UNZIP_TEST_FILE ]]
then
    (cd $DOWNLOADS_DIR && $UN7ZIP $SAT09_ZIP)
fi
if [[ ! -a $SAT18_UNZIP_TEST_FILE ]]
then
    (cd $DOWNLOADS_DIR && $UNZIP $SAT18_ZIP)
fi

for family in $(ls $FAMILIES_DIR)
do
    family_dir="$BENCHMARKS_DIR/$family"
    family_list="$FAMILIES_DIR/$family"
    mkdir -p $family_dir
    for bench in $(cat $family_list)
    do
        bench_to="$family_dir/$bench"
        if [[ ! -a $bench_to ]]
        then
            bench_from=$(find $DOWNLOADS_DIR -name '*'$bench'*' | head -n 1 | grep -E '.*' || (echo Missing: $bench in $family; exit 1))
            cp $bench_from $bench_to
        fi
    done
done
