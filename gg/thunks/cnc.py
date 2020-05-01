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

gg = pygg.init()

solver_path = "../../iglucose/core/iglucose"
march_path = "../../march_cu/march_cu"

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
            f.write(f"a {' '.join(it.chain(a_lits, b_lits))} 0\n")


def run_for_stdout(cmd: List[str]) -> str:
    return sub.run(cmd, check=True, stdout=sub.PIPE).stdout.decode()


def split_outputs(_cnf: pygg.Value, _cube: pygg.Value, n: int) -> List[str]:
    return [f"{out_prefix}{i}" for i in range(2 ** n)]


@gg.thunk_fn(outputs=split_outputs)
def split(cnf: pygg.Value, cube: pygg.Value, n: int) -> pygg.OutputDict:
    appendCubeAsCnf(cnf.path(), cube.path(), "cnf")
    sub.check_call(
        [gg.bin(march_path).path(), "cnf", "-o", out_prefix, "-d", str(n)]
    )
    outputs = {}
    with open(out_prefix, "r") as f:
        for i, l in enumerate(f.readlines()):
            cubeExtend(cube.path(), l, f"{out_prefix}.{i}")
            outputs[f"{out_prefix}{i}"] = gg.file_value(f"{out_prefix}.{i}")
    for j in range(2 ** n)[i:]:
        f = open(f"{out_prefix}.{j}", "w")
        f.close()
        outputs[f"{out_prefix}{j}"] = gg.file_value(f"{out_prefix}.{j}")
    os.remove(out_prefix)
    os.remove("cnf")
    return outputs


@gg.thunk_fn()
def solve(
    cnf: pygg.Value, initial_divides: int, n: int, timeout: float, timeout_factor: float
) -> pygg.Output:
    return gg.thunk(
        solve_, cnf, gg.str_value("a 0"), initial_divides, n, timeout, timeout_factor
    )


@gg.thunk_fn()
def solve_(
    cnf: pygg.Value,
    cube: pygg.Value,
    initial_divides: int,
    n: int,
    timeout: float,
    timeout_factor: float,
) -> pygg.Output:
    # Empty cube as a placeholder
    if cube.as_str() == "":
        return gg.str_value("UNSAT\n")

    output = "s INDETERMINATE"
    if initial_divides == 0:
        merged_cnf = "merge"
        appendCubeAsCnf(cnf.path(), cube.path(), merged_cnf)
        args = [
            gg.bin(solver_path).path(),
            merged_cnf,
            f"-cpu-lim={timeout}",
        ]
        output = run_for_stdout(args)
        os.remove(merged_cnf)
    if "UNSAT" in output:
        return gg.str_value("UNSAT\n")
    elif "s INDETERMINATE" in output:
        if initial_divides != 0:
            n = initial_divides
        sub_queries = gg.thunk(split, cnf, cube, n)
        solve_thunk = []
        for i in range(2 ** n):
            solve_thunk.append(
                gg.thunk(
                    solve_,
                    cnf,
                    sub_queries[f"{out_prefix}{i}"],
                    0,
                    n,
                    timeout * timeout_factor,
                    timeout_factor,
                )
            )
        return functools.reduce(lambda x, y: gg.thunk(merge, x, y), solve_thunk)
    else:
        return gg.str_value("SAT\n")


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


gg.main()
