#! /usr/bin/python3

import sys
import os
import subprocess as sub
import shutil
import functools as ft
import operator as op

if __name__ == '__main__':
    solverPath, CNF, cubeFile, \
        ggCreateThunkPath, ggHashPath, \
        numDivides, timeout, timeoutFactor = sys.argv[1:]

    cnfHash = os.environ['cnf_hash']
    marchHash = os.environ['march_hash']
    ggCreateThunkHash = os.environ['create_thunk_hash']
    ggHashHash = os.environ['hash_hash']
    splitPyHash = os.environ['split_py_hash']
    solvePyHash = os.environ['solve_py_hash']
    mergePyHash = os.environ['merge_py_hash']
    numDivides = int(numDivides)
    timeout = float(timeout)
    timeoutFactor = float(timeoutFactor)

def run_for_stdout(cmd):
    return sub.run(cmd, check=True, stdout=sub.PIPE).stdout.decode()

def run_for_stderr(cmd):
    return sub.run(cmd, check=True, stdout=sub.PIPE).stdout.decode()

def gghash(path):
    ''' Given a path, returns the hash of the referenced file '''
    args = [ggHashPath, path]
    return run_for_stdout(args)

if __name__ == '__main__':
    cubeHash = gghash(cubeFile)

def flatten(lists):
    return ft.reduce(op.add, lists, [])

def envars():
    return [
        '--envar', 'march_hash=%s' % marchHash,
        '--envar', 'create_thunk_hash=%s' % ggCreateThunkHash,
        '--envar', 'hash_hash=%s' % ggHashHash,
        '--envar', 'split_py_hash=%s' % splitPyHash,
        '--envar', 'solve_py_hash=%s' % solvePyHash,
        '--envar', 'merge_py_hash=%s' % mergePyHash,
    ]

def placeholder(t):
    return '@{GGHASH:%s}' % t

def write_split_thunk(path, numDivides):
    splitOutPrefix = 'cube'
    args = [ggCreateThunkPath] +\
        flatten([ ['--output', splitOutPrefix + '.' + str(i)] for i in range(2 ** numDivides) ]) +\
        envars() +\
        [
            '--executable', marchHash,
            '--executable', splitPyHash,
            '--output-path', path,
            '--value', cnfHash,
            '--value', cubeHash,
            '--',
            splitPyHash,
            'split.py',
            placeholder(marchHash),
            placeholder(cnfHash),
            numDivides,
            splitOutPrefix,
        ]
    return run_for_stderr(args)

def write_solve_thunk(path, subCubeHash, numDivides, timeout, timeoutFactor):
    args = [ggCreateThunkPath,
            '--output', 'out',
            '--output', 'split'] +\
        flatten([ ['--output',  'sub%s' % str(i)] for i in range(2 ** numDivides) ]) +\
        envars() +\
        [
            '--executable', solverHash,
            '--executable', solvePyHash,
            '--output-path', path,
            '--value', cnfHash,
            '--value', subCubeHash,
            '--',
            solvePyHash,
            'solve_rec.py',
            placeholder(solverHash),
            placeholder(cnfHash),
            placeholder(subCubeHash),
            solveOutPrefix,
            placeholder(ggCreateThunkHash),
            placeholder(ggHashHash),
            str(numDivides),
            str(timeout),
            str(timeoutFactor),
        ]
    return run_for_stderr(args)


def write_merge_thunk(path, subProblemThunkHashes):
    args = [ggCreateThunkPath,
            '--output', 'out',
        ] +\
        envars() +\
        [
            '--executable', mergePyHash,
            '--output-path', path,
        ] +\
        flatten([['--thunk', s] for s in subProblemThunkHashes]) +\
        [
            '--',
            mergePyHash,
            'merge.py',
        ] +\
        [placeholder(s) for s in subProblemThunkHashes]
    return run_for_stderr(args)

def appendCube(cnfPath, cubePath, mergedPath):
    ''' Glues a CNF file and a cube file, creating an ICNF file '''
    with open(mergedPath, 'w') as o:
        o.write('p inccnf\n')
        with open(cnfPath, 'w') as i:
            for l in i.readlines():
                o.write(l)
        with open(cubePath, 'w') as i:
            for l in i.readlines():
                o.write(l)

def appendCubeAsCnf(cnfPath, cubePath, mergedPath):
    ''' Glues a CNF file and a cube file, creating a CNF file
    Assumes a single cube line.
    '''
    with open(mergedPath, 'w') as out_file:
        cubeToWrite = ""
        numLitsinCube = 0 # Number of literals in the cube
        with open(cubePath, 'r') as in_file:
            line = in_file.readlines()[0]
            print(f"Cube: {line}")
            for lit in line.split()[1:-1]:
                numLitsinCube += 1
                # Adding the literal as a clause
                cubeToWrite+=(f"{lit} 0\n")
        with open(cnfPath, 'r') as in_file:
            for line in in_file.readlines():
                if line[0] == 'p':
                    numClause = int(line.split()[-1])
                    out_file.write(" ".join(line.split()[:-1]) + f" {numClause + numLitsinCube}\n")
                elif line[0] != 'c':
                    out_file.write(line)
        out_file.write(cubeToWrite)

def createEmptyFile(filename):
    f = open(filename, 'w')
    f.close()

def createEmptyThunkFiles(splitThunkName, subThunkName):
    createEmptyFile(splitThunkName)
    for i in range(2 ** numDivides):
        createEmptyFile(f"{subThunkName}{i}")

if __name__ == '__main__':
    mergedCNF = CNF + ".merged"
    appendCube(CNF, cubeFile, mergedCNF)
    args = [solverPath, f"-cpu-lim={timeout}", mergedCNF]
    output = runForStdout(args)
    with open('out', 'w') as out_file:
        if "UNSAT" in output:
            out_file.write("UNSAT\n")
            createEmptyThunkFiles('split', 'sub')
        elif "s INDETERMINATE" in output:
            splitThunkHash = write_split_thunk('split', numDivides)
            solveThunks = []
            for i in range(2 ** numDivides):
                cubeHash = splitThunkHash if i == 0 else splitThunkHash + f"#cube{i}"
                solveThunks.append(write_solve_thunk(f"sub{i}", cubeHash, numDivides,
                                                     timeout * timeoutFactor, timeoutFactor))
            write_merge_thunk('out', solveThunks)
        else:
            out_file.write("SAT\n")
            createEmptyThunkFiles('split', 'sub')
    os.remove(mergedCNF)
