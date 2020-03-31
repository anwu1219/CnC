#! /usr/bin/python3

import sys
import os
import subprocess
import shutil

solverPath, CNF, cubeFile, outPath, \
        ggInit, ggHash, ggCreateThunk, createThunks, \
        marchHash, numDivides, timeout, timeoutFactor \
        splitPyHash, solvePyHash, mergePyHash = sys.argv[1:]

numDivides = int(numDivides)
timeout = int(timeout)
timeoutFactor = int(timeoutFactor)

def run_for_output(cmd):
    o = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
    o = o.stdout.decode()
    return o

newCNF="temp.icnf"
with open(newCNF, 'w') as out_file:
    out_file.write("p inccnf\n")
    with open(CNF, 'r') as in_file:
        for line in in_file.readlines():
            if line[0] != 'c':
                out_file.write(line)
    with open(cubeFile, 'r') as in_file:
        for line in in_file.readlines():
            out_file.write(line)
output = subprocess.run([solverPath, f"-cpu-lim={timeout}", newCNF], check=True, stdout=subprocess.PIPE)
output = output.stdout.decode()
with open(outPath, 'w') as out_file:
    if "s UNSAT" in output:
        out_file.write("UNSAT\n")
    elif "s INDETERMINATE" in output:
        newCNFHash = run_for_output([ggHash, newCNF]).strip()
        solverHash = run_for_output([ggHash, solverPath]).strip()

        subprocess.run([ggInit], check=True)
        # Write some thunks.
        subprocess.run([
                createThunks,
                spli

            ], check=True)
        # See output.thunk for the created thunk.
        shutil.rmtree(".gg")
    else:
        out_file.write("SAT\n")
os.remove(newCNF)
