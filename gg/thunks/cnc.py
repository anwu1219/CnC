#!/usr/bin/env python3.7
# ARGS: fib 5
# RESULT: 5
# Copied
import pygg
from pygg import Value, Output, OutputDict
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


class CubePlusCnf(object):
    """ Appends a cube to a cnf, and truncates when the object is dropped """

    path: str
    cnf_orig_size: int
    alternate_cnf: str

    def __init__(self, cnf_path: str, cube_path: str):
        self.cnf_orig_size = os.path.getsize(cnf_path)
        self.path = cnf_path
        with open(cnf_path, "a") as cnf_file:
            with open(cube_path, "r") as cube_file:
                # We're invalidating the header. Must notify solvers.
                cnf_file.writelines(
                    [f"{l} 0\n" for l in cube_file.readlines()[0].split()[1:-1]]
                )

    def __del__(self):
        os.truncate(self.path, self.cnf_orig_size)


def cubeExtend(pathA: str, lineB: str, outputPath: str) -> None:
    with open(pathA, "r") as a:
        with open(outputPath, "w") as f:
            a_lits = a.read().strip().split()[1:-1]
            b_lits = lineB.strip().split()[1:-1]
            print(f"\nCube CREATE: a {' '.join(it.chain(a_lits, b_lits))} 0\n")
            f.write(f"a {' '.join(it.chain(a_lits, b_lits))} 0\n")


def split_outputs(_cnf: Value, _cube: Value, n: int) -> List[str]:
    return [f"{out_prefix}{i}" for i in range(2 ** n)]


@gg.thunk_fn(outputs=split_outputs)
def split(cnf: Value, cube: Value, n: int) -> OutputDict:
    print(f"\nCube TIMEOUT {cube.as_str()}")
    new_cnf = CubePlusCnf(cnf.path(), cube.path())
    res = sub.run(
        [gg.bin(march_path).path(), new_cnf.path, "-o", out_prefix, "-d", str(n)]
    )
    outputs = {}
    k = 0
    if res.returncode == 20:
        # No cubes, we are unsat!
        pass
    elif res.returncode == 0:
        with open(out_prefix, "r") as f:
            for i, l in enumerate(f.readlines()):
                cubeExtend(cube.path(), l, f"{out_prefix}.{i}")
                outputs[f"{out_prefix}{i}"] = gg.file_value(f"{out_prefix}.{i}")
                k += 1;
    else:
        raise ValueError(f"Unexpected march return code: {res.returncode}")
    for j in range(2 ** n)[k:]:
        f = open(f"{out_prefix}.{j}", "w")
        f.close()
        outputs[f"{out_prefix}{j}"] = gg.file_value(f"{out_prefix}.{j}")
    os.remove(out_prefix)
    del new_cnf
    return outputs


@gg.thunk_fn()
def solve(
    cnf: Value,
    initial_divides: int,
    n: int,
    timeout: float,
    timeout_factor: float,
    fut: int,
) -> Output:
    return gg.thunk(
        solve_,
        cnf,
        gg.str_value("a 0"),
        initial_divides,
        n,
        timeout,
        timeout_factor,
        fut,
    )

def run_solver(path: str, timeout: int) -> str:
    """ returns a string: 'SAT' 'UNSAT' or '' """
    args = [
        gg.bin(solver_path).path(),
        path,
        "-f",
        "-t",
        f"{int(timeout+0.5)}",
        "-q",
    ]
    res = sub.run(args, stdout=sub.PIPE, stderr=sub.PIPE)
    out = res.stdout.decode()
    err = res.stderr.decode()
    exitCode = res.returncode
    if exitCode == 20 or "s UNSAT" in out:
        return "UNSAT"
    elif exitCode == 10 or "s SAT" in err:
        return "SAT"
    elif exitCode == 0:
        return ""
    else:
        print("Output:", out)
        print("Error:", err)
        raise Exception("Unknown base solve result. Exit code: " + str(exitCode))


@gg.thunk_fn()
def solve_(
    cnf: Value,
    cube: Value,
    initial_divides: int,
    n: int,
    timeout: float,
    timeout_factor: float,
    fut: int,
) -> Output:
    # Empty cube as a placeholder
    if cube.as_str() == "":
        return gg.str_value("UNSAT\n")

    result = ""
    if initial_divides == 0:
        new_cnf = CubePlusCnf(cnf.path(), cube.path())
        result = run_solver(new_cnf.path, min(800, timeout))
        del new_cnf
    if result == "UNSAT":
        print(f"\nCube UNSAT {cube.as_str()}")
        return gg.str_value("UNSAT\n")
    elif result == "":
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
                    fut,
                )
            )
        if fut != 0:
            return functools.reduce(lambda x, y: gg.thunk(merge, x, y), solve_thunk)
        else:
            return functools.reduce(lambda x, y: gg.thunk(merge_no_fut, x, y), solve_thunk)
    elif result == "SAT":
        return gg.str_value("SAT\n")
    else:
        raise Exception("Bad result: " + result)


@gg.thunk_fn()
def merge(r1: Optional[Value], r2: Optional[Value]) -> Output:
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
def merge_no_fut(r1: Value, r2: Value) -> Output:
    r1_str = r1.as_str()
    r2_str = r2.as_str()
    if r1_str == "UNSAT\n" and r2_str == "UNSAT\n":
        return gg.str_value("UNSAT\n")
    else:
        return gg.str_value("SAT\n")


gg.main()
