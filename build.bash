#!/usr/bin/env bash

# Enable exit-on-error, and command log
set -xe


# Fetch the solvers
git submodule init
git submodule update --recursive
./fetch_painless.bash

# Build the solvers
(cd march_cu && make -j$(nproc))
(cd iglucose/core && make -j$(nproc) rs && cd ../simp && make -j$(proc))
(cd lingeling && ./configure.sh -static && make -j $(nproc))
(cd cadical && env CXXFLAGS=-static ./configure && cd build && make -j $(nproc))
(cd painless-v2 && make -j$(nproc))
