#!/usr/bin/env python3
import sys
import subprocess
import os

numDivides = sys.argv[1]
numDivides = int(numDivides)

files = sys.argv[2:]

with open("out", "w") as fout:
    for f in files:
        with open(f, "r") as fin:
            if "UNSAT" not in fin.read():
                fout.write("SAT\n")
                sys.exit(0)
    fout.write("UNSAT\n")
