#! /usr/bin/python3

import sys
import os
import subprocess
import shutil


if len(sys.argv[1:]) < 5:
    solverPath, CNF, cubeFile, outPath = sys.argv[1:]
    timeout = 1
    timeoutFactor = 2
else:
    solverPath, CNF, cubeFile, outPath, \
        ggCreateThunk, \
        numDivides, timeout, timeoutFactor = sys.argv[1:]

    marchHash = os.environ['march_hash']
    createThunkHash = os.environ['create_thunk_hash']
    splitPyHash = os.environ['split_py_hash']
    solvePyHash = os.environ['solve_py_hash']
    mergePyHash = os.environ['merge_py_hash']
    numDivides = int(numDivides)
    timeout = int(timeout)
    timeoutFactor = int(timeoutFactor)

def write_split_thunk(path, numDivides, timeout, timeoutFactor):
    args = [ggCreateThunk]

def run_for_output(cmd):
    o = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
    o = o.stdout.decode()
    return o

newCNF="temp.cnf"
with open(newCNF, 'w') as out_file:
    cubeToWrite = ""
    numLitsinCube = 0 # Number of literals in the cube
    with open(cubeFile, 'r') as in_file:
        for line in in_file.readlines():
            print(f"Cube: {line}")
            for lit in line.split()[1:-1]:
                numLitsinCube += 1
                # Adding the literal as a clause
                cubeToWrite+=(f"{lit} 0\n")
            break
    with open(CNF, 'r') as in_file:
        for line in in_file.readlines():
            if line[0] == 'p':
                numClause = int(line.split()[-1])
                out_file.write(" ".join(line.split()[:-1]) + f" {numClause + numLitsinCube}\n")
            elif line[0] != 'c':
                out_file.write(line)
    out_file.write(cubeToWrite)
output = subprocess.run([solverPath, f"-cpu-lim={timeout}", newCNF], check=True, stdout=subprocess.PIPE)
output = output.stdout.decode()
with open(outPath, 'w') as out_file:
    if "UNSAT" in output:
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
