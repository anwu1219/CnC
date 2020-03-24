#!/usr/bin/python3
import sys
import subprocess
import os

marchPath, CNF, numDivides, outPrefix = sys.argv[1:]
numDivides = int(numDivides)

subprocess.run([marchPath, CNF, "-o", outPrefix, "-l", str(2 ** numDivides)], check = True)

with open(outPrefix, "r") as f:
    for i, l in enumerate(f.readlines()):
        with open(f"{outPrefix}.{i}", "w") as fout:
            fout.write(l)
os.remove(outPrefix)
