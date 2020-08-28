#!/usr/bin/env python3.7
# ARGS: fib 5
# RESULT: 5
# Copied
import pygg
import os
import functools
import subprocess as sub
import tempfile
import itertools as it
from typing import List, Optional

import sys
sys.setrecursionlimit(5000)

gg = pygg.init()

solver_path = "cadical"
march_path = "march_cu"

gg.install(solver_path)
gg.install(march_path)

out_prefix = "cube"

def appendCubeAsCnf(cnfPath: str, cubePath: str, mergedPath: str) -> None:
    """ Glues a CNF file and a cube file, creating a CNF file
    Assumes a single cube line.
    """
    with open(mergedPath, "w") as out_file:
        cubeToWrite = ""
        numLitsinCube = 0  # Number of literals in the cube
        with open(cubePath, "r") as in_file:
            line = in_file.readlines()[0]
            for lit in line.split()[1:-1]:
                numLitsinCube += 1
                # Adding the literal as a clause
                cubeToWrite += f"{lit} 0\n"
        with open(cnfPath, "r") as in_file:
            for line in in_file.readlines():
                if line[0] == "p":
                    numClause = int(line.split()[-1])
                    out_file.write(
                        " ".join(line.split()[:-1]) + f" {numClause + numLitsinCube}\n"
                    )
                elif line[0] != "c":
                    out_file.write(line)
        out_file.write(cubeToWrite)


def cubeExtend(pathA: str, lineB: str, outputPath: str) -> None:
    with open(pathA, "r") as a:
        with open(outputPath, "w") as f:
            a_lits = a.read().strip().split()[1:-1]
            b_lits = lineB.strip().split()[1:-1]
            print(f"\nCube CREATE: a {' '.join(it.chain(a_lits, b_lits))} 0\n")
            f.write(f"a {' '.join(it.chain(a_lits, b_lits))} 0\n")


def run_for_stdout(cmd: List[str]) -> str:
    return sub.run(cmd, check=True, stdout=sub.PIPE).stdout.decode()


def split_outputs(_cnf: pygg.Value, _cube: pygg.Value, n: int) -> List[str]:
    return [f"{out_prefix}{i}" for i in range(2 ** n)]


@gg.thunk_fn(outputs=split_outputs)
def split(cnf: pygg.Value, cube: pygg.Value, n: int) -> pygg.OutputDict:
    print(f"\nCube TIMEOUT {cube.as_str()}")
    appendCubeAsCnf(cnf.path(), cube.path(), "cnf")
    sub.check_call(
        [gg.bin(march_path).path(), "cnf", "-o", out_prefix, "-d", str(n)]
    )
    outputs = {}
    k = 0
    with open(out_prefix, "r") as f:
        for i, l in enumerate(f.readlines()):
            cubeExtend(cube.path(), l, f"{out_prefix}.{i}")
            outputs[f"{out_prefix}{i}"] = gg.file_value(f"{out_prefix}.{i}")
            k += 1;
    for j in range(2 ** n)[k:]:
        f = open(f"{out_prefix}.{j}", "w")
        f.close()
        outputs[f"{out_prefix}{j}"] = gg.file_value(f"{out_prefix}.{j}")
    os.remove(out_prefix)
    os.remove("cnf")
    return outputs


@gg.thunk_fn()
def solve(
        cnf: pygg.Value, initial_divides: int, n: int, timeout: float, timeout_factor: float,
        fut : int
) -> pygg.Output:
    return gg.thunk(
        solve_, cnf, gg.str_value("a 0"), initial_divides, n, timeout, timeout_factor, fut
    )

@gg.thunk_fn()
def solve_(
    cnf: pygg.Value,
    cube: pygg.Value,
    initial_divides: int,
    n: int,
    timeout: float,
    timeout_factor: float,
    fut : int
) -> pygg.Output:
    # Empty cube as a placeholder
    if cube.as_str() == "":
        return gg.str_value("UNSAT\n")

    exitCode = 0
    if initial_divides == 0:
        merged_cnf = "merge"
        appendCubeAsCnf(cnf.path(), cube.path(), merged_cnf)
        args = [
            gg.bin(solver_path).path(),
            merged_cnf,
            "-t",
            f"{int(timeout + 0.5)}",
        ]
        exitCode = sub.run(args).returncode
        os.remove(merged_cnf)
    if exitCode == 20:
        print(f"\nCube UNSAT {cube.as_str()}")
        return gg.str_value("UNSAT\n")
    elif exitCode == 0:
        divides = n if initial_divides == 0 else initial_divides
        sub_queries = gg.thunk(split, cnf, cube, divides)
        solve_thunk = []
        for i in range(2 ** divides):
            solve_thunk.append(
                gg.thunk(
                    solve_,
                    cnf,
                    sub_queries[f"{out_prefix}{i}"],
                    0,
                    n,
                    timeout * timeout_factor,
                    timeout_factor,
                    fut
                )
            )
        if fut != 0:
            return functools.reduce(lambda x, y: gg.thunk(merge, x, y), solve_thunk)
        else:
            return functools.reduce(lambda x, y: gg.thunk(merge_no_fut, x, y), solve_thunk)
    elif exitCode == 10:
        return gg.str_value("SAT\n")
    else:
        raise Exception("Unexpected exit code from base solver!")

@gg.thunk_fn()
def merge(r1: Optional[pygg.Value], r2: Optional[pygg.Value]) -> pygg.Output:
    if r2 is not None and r2.as_str() == "SAT\n":
        # r2 is SAT, return SAT
        return r2
    elif r1 is not None and r1.as_str() == "SAT\n":
        # see aboce
        return r1
    elif r1 is None or r2 is None:
        # Something is unresolved, and not SATs yet...
        return gg.this()
    else:
        # All is resolved, no SATs
        return r1

@gg.thunk_fn()
def merge_no_fut(r1: pygg.Value, r2: pygg.Value) -> pygg.Output:
    r1_str = r1.as_str()
    r2_str = r2.as_str()
    if r1_str == "UNSAT\n" and r2_str == "UNSAT\n":
        return gg.str_value("UNSAT\n")
    else:
        return gg.str_value("SAT\n")

gg.main()
