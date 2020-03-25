#!/usr/bin/python3
import sys
import subprocess
import os

numDivides, output = sys.argv[1:3]
numDivides = int(numDivides)

files = sys.argv[3:]

with open(output, "w") as fout:
    for f in files:
        with open(f, "r") as fin:
            if "UNSAT" not in fin.read():
                fout.write("SAT\n")
                sys.exit(0)
    fout.write("UNSAT\n")
