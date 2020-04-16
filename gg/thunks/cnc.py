#!/usr/bin/env python3.7
# ARGS: fib 5
# RESULT: 5
# Copied
import os, sys
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

if not os.path.exists(sys.argv[1]):
    import pygg
else:
    spec = spec_from_loader(
        "pygg", SourceFileLoader("pygg", os.path.realpath(sys.argv[1]))
    )
    pygg = module_from_spec(spec)
    spec.loader.exec_module(pygg) # type: ignore
    del sys.argv[1]

# End copy

import functools
import subprocess as sub
import tempfile
from typing import List

solver_path = "../../iglucose/core/iglucose"
march_path = "../../march_cu/march_cu"

pygg.install(solver_path)
pygg.install(march_path)

out_prefix = "cube"

def appendCubeAsCnf(cnfPath, cubePath, mergedPath):
    ''' Glues a CNF file and a cube file, creating a CNF file
    Assumes a single cube line.
    '''
    with open(mergedPath, 'w') as out_file:
        cubeToWrite = ""
        numLitsinCube = 0 # Number of literals in the cube
        with open(cubePath, 'r') as in_file:
            line = in_file.readlines()[0]
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

def run_for_stdout(cmd):
    return sub.run(cmd, check=True, stdout=sub.PIPE).stdout.decode()

def split_outputs(gg : pygg.GG, cnf : pygg.Value, n : int)->List[str]:
    return [f"{out_prefix}{i}" for i in range(2 ** n)]

@pygg.thunk_fn(outputs=split_outputs)
def split(gg: pygg.GG, cnf : pygg.Value, n : int) -> pygg.MultiOutput:
    sub.check_call([gg.bin(march_path).path(), cnf.path(),
                    "-o", out_prefix, "-l", str(2 ** n)])
    outputs = {}
    with open(out_prefix, "r") as f:
        for i, l in enumerate(f.readlines()):
            with open(f"{out_prefix}.{i}", "w") as fout:
                fout.write(l)
            outputs[f"{out_prefix}{i}"] = gg.file_value(f"{out_prefix}.{i}")
    for j in range(2 **n)[i:]:
        f = open(f"{out_prefix}.{j}", "w")
        f.close()
        outputs[f"{out_prefix}{j}"] = gg.file_value(f"{out_prefix}.{j}")
    os.remove(out_prefix)
    return outputs

@pygg.thunk_fn()
def solve(gg : pygg.GG, cnf : pygg.Value, n : int, timeout : float,
          timeout_factor : float) -> pygg.Output:
    return gg.thunk(solve_, [cnf, gg.str_value("a 0"), n ,timeout,
                             timeout_factor])

@pygg.thunk_fn()
def solve_(gg : pygg.GG, cnf : pygg.Value, cube : pygg.Value, n : int,
           timeout : float, timeout_factor : float) -> pygg.Output:
    # Empty cube as a placeholder
    if cube.as_str() == "":
        return gg.str_value("UNSAT\n")

    merged_cnf = "merge"
    appendCubeAsCnf(cnf.path(), cube.path(), merged_cnf)
    args = [gg.bin(solver_path).path(), merged_cnf, f"-cpu-lim={timeout}", ]
    output = run_for_stdout(args)
    if "UNSAT" in output:
        os.remove(merged_cnf)
        return gg.str_value("UNSAT\n")
    elif "s INDETERMINATE" in output:
        merged_cnf_val = gg.file_value(merged_cnf)
        sub_queries = gg.thunk(split, [merged_cnf_val, n])
        solve_thunk = []
        for i in range(2 ** n):
            solve_thunk.append( gg.thunk(solve_, [merged_cnf_val, sub_queries[f"{out_prefix}{i}"],
                                                  n, timeout * timeout_factor, timeout_factor]) )
        return functools.reduce(lambda x, y : gg.thunk(merge, [x, y]), solve_thunk)
    else:
        os.remove(merged_cnf)
        return gg.str_value("SAT\n")

@pygg.thunk_fn()
def merge(gg : pygg.GG, r1 : pygg.Value, r2 : pygg.Value)->pygg.Output:
    r1_str = r1.as_str()
    r2_str = r2.as_str()
    if r1_str == "UNSAT\n" and r2_str == "UNSAT\n":
        return gg.str_value("UNSAT\n")
    else:
        return gg.str_value("SAT\n")

pygg.main()
