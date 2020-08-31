#!/usr/bin/env python3

"""gg-view

Usage:
  gg-view.py [options] <thunk-hash>

Options:
  -h --help             Show this screen.
"""

from docopt import docopt
from json import loads
from glob import glob
from typing import Any, List, NamedTuple, Optional, Tuple, Set
from os import environ
from os.path import exists, abspath, dirname, join, basename, split
from pprint import pprint
from re import match
import re
import shutil
import subprocess as sub
from time import time


class Hash(NamedTuple):
    as_str: str

    def __str__(self) -> str:
        return self.as_str

    def tag(self) -> str:
        return self.as_str[0]


def check_for_logs():
    if (
        not exists(".gg/renames")
        or not exists(".gg/reductions")
        or not exists(".gg/metadata")
    ):
        raise ValueError(
            "Cannot view the computation graph because some metadata was not recorded.\nDid you run gg-force with -M and -r?"
        )


def main():
    arguments = docopt(__doc__)
    # next_node_id = 0
    # hashes_to_node = {}
    nodes: List[Tuple[Hash, str]] = []
    edges: List[Tuple[Hash, Hash]] = []
    start: Hash = Hash(arguments["<thunk-hash>"])
    queue: List[Hash] = [start]
    queued: Set[Hash] = {start}
    # start_id = next_node_id
    # next_node_id += 1
    # labels.append(start)
    while len(queue) > 0:
        h_init = queue.pop()
        h = h_init
        deps = set()
        times: List[float] = []
        assert h is not None
        while h.tag() != "V":
            for d in get_deps(h):
                deps.add(d)
            t = get_time(h)
            if t is not None:
                times.append(t)
            h = get_reduction(h)
            ts = "".join(f"\n{t}" for t in times)
        nodes.append((h_init, hash_label(h_init) + ts + "\n" + hash_label(h)))
        for d in deps:
            if d.tag() != "V":
                edges.append((h_init, d))
                if d not in queued:
                    queue.append(d)
                    queued.add(d)
    print("digraph D {")
    for (n, l) in nodes:
        print(f'  "{n}" [label="{l}"]')
    for (a, b) in edges:
        print(f'  "{a}" -> "{b}"')
    print("}")


def get_thunk(h: Hash):
    if exists(f".gg/blobs/{h}"):
        r = sub.run(
            ["gg-describe", h.as_str], stderr=sub.DEVNULL, stdout=sub.PIPE, check=True
        )
        output = r.stdout.decode()
        return loads(output)
    else:
        return None


def get_time(h: Hash) -> Optional[float]:
    m = f".gg/metadata/{h}"
    if exists(m):
        return float(open(m).read().strip().split()[2])
    else:
        return None


def get_reduction(h: Hash) -> Hash:
    assert h.tag() == "T"
    r = f".gg/reductions/{h}"
    n = f".gg/renames/{h}"
    if exists(r):
        return Hash(open(r).read().strip())
    elif exists(n):
        return Hash(open(n).read().strip())
    else:
        raise ValueError(f"Hash {h} is not reduced or renamed")


def hash_label(h: Optional[Hash]) -> str:
    if h is None:
        return "None"
    elif h.tag() == "V":
        with open(f".gg/blobs/{h}", "rb") as f:
            o = f.read(10)
            try:
                s = o.decode()
                if s.isprintable() and '"' not in s:
                    return s
                else:
                    return h.as_str[:6]
            except:
                return h.as_str[:6]
        return "V"
    else:
        return h.as_str[:6]


def get_deps(h: Hash) -> List[Hash]:
    if h.tag() == "T":
        if "#" in str(h):
            return []
        else:
            thunk = get_thunk(h)
            if thunk is None:
                return []
            return list(
                map(
                    Hash,
                    thunk["values"]
                    + thunk["executables"]
                    + thunk["thunks"]
                    + thunk["futures"],
                )
            )
    else:
        return []


main()
