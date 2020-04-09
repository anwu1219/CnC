#!/usr/bin/env python3

import sys
import os
import subprocess as sub
import shutil
import functools as ft
import operator as op
from typing import List, TypeVar, NamedTuple, Optional
from pathlib import Path


class ExecHashes(NamedTuple):
    """ A collection of executable hashes
    """

    march_hash: str
    solver_hash: str
    solve_py_hash: str
    merge_py_hash: str
    split_py_hash: str
    gg_create_thunk_hash: str
    gg_hash_hash: str

    @classmethod
    def from_env(cls) -> "ExecHashes":
        return cls(
            march_hash=os.environ["march_hash"],
            solver_hash=os.environ["solver_hash"],
            solve_py_hash=os.environ["solve_py_hash"],
            merge_py_hash=os.environ["merge_py_hash"],
            split_py_hash=os.environ["split_py_hash"],
            gg_create_thunk_hash=os.environ["gg_create_thunk_hash"],
            gg_hash_hash=os.environ["gg_hash_hash"],
        )

    def as_gg_arglist(self) -> List[str]:
        return [
            "--envar",
            "march_hash=%s" % self.march_hash,
            "--envar",
            "solver_hash=%s" % self.solver_hash,
            "--envar",
            "gg_create_thunk_hash=%s" % self.gg_create_thunk_hash,
            "--envar",
            "gg_hash_hash=%s" % self.gg_hash_hash,
            "--envar",
            "split_py_hash=%s" % self.split_py_hash,
            "--envar",
            "solve_py_hash=%s" % self.solve_py_hash,
            "--envar",
            "merge_py_hash=%s" % self.merge_py_hash,
        ]


def run_for_stdout(cmd: List[str]) -> str:
    return sub.run(cmd, check=True, stdout=sub.PIPE).stdout.decode()


def run_for_stderr(cmd: List[str]) -> str:
    return sub.run(cmd, check=True, stderr=sub.PIPE).stderr.decode()


def run_create_thunk(
    gg_create_thunk_path: str, ehashes: ExecHashes, args: List[str]
) -> str:
    args = [gg_create_thunk_path] + ehashes.as_gg_arglist() + args
    print(args)
    r = run_for_stderr(args).strip()
    print(r)
    return r


T = TypeVar("T")


def flatten(lists: List[List[T]]) -> List[T]:
    return ft.reduce(op.add, lists, [])


def placeholder(t: str) -> str:
    return "@{GGHASH:%s}" % t


def write_split_thunk(
    gg_create_thunk_path: str,
    path: str,
    cnf_hash: str,
    cube_hash: str,
    ehashes: ExecHashes,
    num_divides: int,
) -> str:
    return run_create_thunk(
        gg_create_thunk_path,
        ehashes,
        flatten([["--output", f"cube{i}"] for i in range(2 ** num_divides)])
        + [
            "--executable",
            ehashes.march_hash,
            "--executable",
            ehashes.split_py_hash,
            "--output-path",
            path,
            "--value",
            cnf_hash,
            "--value",
            cube_hash,
            "--",
            ehashes.split_py_hash,
            "splitter.py",
            placeholder(ehashes.march_hash),
            placeholder(cnf_hash),
            placeholder(cube_hash),
            str(num_divides),
        ],
    )


def write_solve_thunk(
    gg_create_thunk_path: str,
    path: Optional[str],
    ehashes: ExecHashes,
    cnf_hash: str,
    cube_hash: str,
    num_divides: int,
    timeout: float,
    timeout_factor: float,
    placeholder_: Optional[str] = None,
) -> str:
    return run_create_thunk(
        gg_create_thunk_path,
        ehashes,
        ["--output", "out", "--output", "split"]
        + flatten([["--output", f"sub{i}"] for i in range(2 ** num_divides)])
        + ["--executable", ehashes.solver_hash, "--executable", ehashes.solve_py_hash,]
        + ([] if path is None else ["--output-path", path])
        + ([] if placeholder_ is None else ["--placeholder", placeholder_])
        + [
            "--value",
            cnf_hash,
            "--value" if cube_hash[0] == 'V' else '--thunk',
            cube_hash,
            "--",
            ehashes.solve_py_hash,
            "solve_rec.py",
            placeholder(ehashes.solver_hash),
            placeholder(cnf_hash),
            placeholder(cube_hash),
            placeholder(ehashes.gg_create_thunk_hash),
            placeholder(ehashes.gg_hash_hash),
            str(num_divides),
            str(timeout),
            str(timeout_factor),
        ],
    )


def write_merge_thunk(
    gg_create_thunk_path: str,
    path: str,
    ehashes: ExecHashes,
    num_divides: int,
    sub_thunk_hahes: List[str],
) -> str:
    return run_create_thunk(
        gg_create_thunk_path,
        ehashes,
        [
            "--output",
            "out",
            "--executable",
            ehashes.merge_py_hash,
            "--output-path",
            path,
        ]
        + flatten([["--thunk", s] for s in sub_thunk_hahes])
        + ["--", ehashes.merge_py_hash, "merge.py", str(num_divides)]
        + [placeholder(s) for s in sub_thunk_hahes],
    )


def append_cube(cnf_path, cube_path, merged_path):
    """ Glues a CNF file and a cube file, creating an ICNF file """
    with open(merged_path, "w") as o:
        o.write("p inccnf\n")
        with open(cnf_path, "r") as i:
            for l in i.readlines():
                o.write(l)
        with open(cube_path, "r") as i:
            for l in i.readlines():
                o.write(l)


def touch_output_files(num_divides: int):
    Path("out").touch()
    Path("split").touch()
    for i in range(2 ** num_divides):
        Path(f"sub{i}").touch()


def main():
    (
        solver_path,
        cnf_path,
        cube_path,
        gg_create_thunk_path,
        gg_hash_path,
        num_divides,
        timeout,
        timeout_factor,
    ) = sys.argv[1:]

    ehashes = ExecHashes.from_env()
    num_divides = int(num_divides)
    timeout = float(timeout)
    timeout_factor = float(timeout_factor)

    cube_hash = run_for_stdout([gg_hash_path, cube_path]).strip()
    cnf_hash = run_for_stdout([gg_hash_path, cnf_path]).strip()

    icnf_path = f"icnf"
    append_cube(cnf_path, cube_path, icnf_path)
    print("Starting solver")
    output = run_for_stdout([solver_path, f"-cpu-lim={timeout}", icnf_path])
    os.remove(icnf_path)
    if "UNSAT" in output:
        touch_output_files(num_divides)
        with open("out", "w") as out_file:
            out_file.write("UNSAT\n")
    elif "s INDETERMINATE" in output:
        print("Timed out. Splitting")
        split_hash = write_split_thunk(
            gg_create_thunk_path, "split", cnf_hash, cube_hash, ehashes, num_divides
        )
        cube_thunks = []
        for i in range(2 ** num_divides):
            sub_cube_hash = split_hash + ("" if i == 0 else f"#cube{i}")
            cube_thunks.append(
                write_solve_thunk(
                    gg_create_thunk_path,
                    f"sub{i}",
                    ehashes,
                    cnf_hash,
                    sub_cube_hash,
                    num_divides,
                    timeout * timeout_factor,
                    timeout_factor,
                )
            )
        write_merge_thunk(gg_create_thunk_path, "out", ehashes, num_divides, cube_thunks)
    else:
        touch_output_files(num_divides)
        with open("out", "w") as out_file:
            out_file.write("SAT\n")


if __name__ == "__main__":
    main()
