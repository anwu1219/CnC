#!/usr/bin/env python3

from solve_rec import ExecHashes, run_for_stdout, write_solve_thunk
import os
import sys
import shutil
import subprocess as sub
from typing import List

def which(pgm: str) -> str:
    r = shutil.which(pgm)
    assert r is not None, f"Unknown program: {pgm}"
    return r

def gg_hash(path: str) -> str:
    return run_for_stdout([which("gg-hash-static"), path]).strip()


def gg_collect(paths: List[str]):
    sub.check_call([which("gg-collect")] + paths)


def gg_init():
    sub.check_call([which("gg-init")])


def main():
    cnc_dir, cnf_path, num_divides, timeout, timeout_factor = sys.argv[1:]
    num_divides = int(num_divides)
    timeout = float(timeout)
    timeout_factor = float(timeout_factor)

    march_path = os.path.join(cnc_dir, "march_cu", "march_cu")
    solver_path = os.path.join(cnc_dir, "iglucose", "core", "iglucose")
    solve_py_path = os.path.join(cnc_dir, "gg", "scripts", "solve_rec.py")
    split_py_path = os.path.join(cnc_dir, "gg", "scripts", "splitter.py")
    merge_py_path = os.path.join(cnc_dir, "gg", "scripts", "merge.py")
    gg_create_thunk_path = which("gg-create-thunk-static")
    gg_hash_path = which("gg-hash-static")

    cube_path = "emptycube"
    with open(cube_path, "w") as f:
        f.writelines(["a 0"])

    gg_init()
    gg_collect(
        [
            march_path,
            solver_path,
            solve_py_path,
            split_py_path,
            merge_py_path,
            gg_create_thunk_path,
            gg_hash_path,
            cnf_path,
            cube_path,
        ]
    )
    env = ExecHashes(
        march_hash=gg_hash(march_path),
        solver_hash=gg_hash(solver_path),
        solve_py_hash=gg_hash(solve_py_path),
        merge_py_hash=gg_hash(merge_py_path),
        split_py_hash=gg_hash(split_py_path),
        gg_create_thunk_hash=gg_hash(gg_create_thunk_path),
        gg_hash_hash=gg_hash(gg_hash_path),
    )
    write_solve_thunk(
        gg_create_thunk_path,
        None,
        env,
        gg_hash(cnf_path),
        gg_hash(cube_path),
        num_divides,
        timeout,
        timeout_factor,
        "output.thunk",
    )

if __name__ == "__main__":
    main()
