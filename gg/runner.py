#!/usr/bin/env python3

"""gg-Marabou test runner

Usage:
  runner.py run [options] <benchmark>
  runner.py list
  runner.py (-h | --help)

Options:
  --jobs N              The number of jobs [default: 1]
  --initial-divides N   The initial number of divides [default: 0]
  --online-divides N    The number of divides to do on timeout [default: 2]
  --future-mode     S   The divide strategy [default: false]
  --timeout N           How long to try for (s) [default: 3600]
  --initial-timeout N   How long to try for (s) before splitting [default: 5]
  --timeout-factor N    How long to multiply the initial_timeout by each split [default: 1.5]
  --infra I             gg-local, gg-lambda [default: gg-local]
  --trial N             the trial number to run [default: 0]
  -h --help             Show this screen.
"""

from exp import Observation, Input, Runner, SDict

from docopt import docopt
from glob import glob
from typing import Any, List, NamedTuple
from os import environ
from os.path import exists, abspath, dirname, join, basename
from pprint import pprint
from re import match
import shutil
import subprocess as sub
from time import time

SCRIPT_DIR = abspath(dirname(abspath(__file__)))
BENCHMARKS_DIR = f"{SCRIPT_DIR}/benchmarks"


def which(s: str) -> str:
    r = shutil.which(s)
    assert r is not None
    return r


MARCH_DIR_PATH = abspath("../march_cu")
GLUC_PATH = abspath("../iglucose/core/")
CNC_PATH = abspath("./thunks/cnc.py")
FORCE_PATH = which("gg-force")

environ["PATH"] = f"{MARCH_DIR_PATH}:{GLUC_PATH}:" + environ["PATH"]


def main() -> None:
    arguments = docopt(__doc__)
    r = Runner(SCRIPT_DIR, CncInput, CncOutput)  # type: Runner[CncInput, CncOutput]
    if arguments["run"]:
        arguments["--benchmark"] = basename(search(arguments["<benchmark>"]))
        a = CncInput(arguments)
        res = r.run(a)
        pprint(res)
    elif arguments["list"]:
        r.list()
    else:
        print("Missing command!")


def argize(s: str) -> str:
    assert match("[a-z0-9_]*", s)
    return "--" + s.replace("_", "-")


def parse(ty: type, s: str) -> Any:
    if ty == str or ty == int or ty == float:
        return ty(s)
    elif ty == bool:
        if s.lower() == "true":
            return True
        elif s.lower() == "false":
            return False
        else:
            raise ValueError(f"Invalid boolean: '{s}' (True and False are acceptable)")
    else:
        raise ValueError(f"Unparsable type: {ty} for '{s}'")


def search(s: str) -> str:
    r = glob(f"{BENCHMARKS_DIR}/**/*{s}*", recursive=True)
    if len(r) == 1:
        return r[0]
    elif len(r) == 0:
        print(f"No benchmark found containing '{s}'")
        exit(1)
    else:
        print(f"Multiple benchmarks found:")
        for f in r:
            print(f"  {f}")
        exit(1)


class CncOutput(Observation):
    duration: float
    result: str
    family: str

    def __init__(self, result: str, duration: float, family: str):
        for attr, ty in self.__annotations__.items():
            self.__setattr__(attr, locals()[attr])

    @staticmethod
    def default_values() -> SDict:
        return {}

    def values(self) -> SDict:
        return {attr: str(self.__getattribute__(attr)) for attr in self.__annotations__}

    @staticmethod
    def fields() -> List[str]:
        return [
            "duration",
            "result",
            "family",
        ]


class CncInput(Input[CncOutput]):
    benchmark: str
    jobs: int
    infra: str
    initial_divides: int
    online_divides: int
    initial_timeout: float
    timeout_factor: float
    timeout: int
    future_mode: bool
    trial: int

    def __init__(self, args):
        for attr, ty in self.__annotations__.items():
            self.__setattr__(attr, args[argize(attr)])

    @staticmethod
    def default_values() -> SDict:
        return {}

    def values(self) -> SDict:
        return {attr: str(self.__getattribute__(attr)) for attr in self.__annotations__}

    @staticmethod
    def fields() -> List[str]:
        return [
            "benchmark",
            "jobs",
            "infra",
            "initial_divides",
            "online_divides",
            "initial_timeout",
            "timeout_factor",
            "timeout",
            "future_mode",
            "trial",
        ]

    def run(self, working_dir: str) -> CncOutput:
        path = search(self.benchmark)
        family = basename(dirname(path))
        if self.infra in ["gg-local", "gg-lambda"]:
            sub.run(
                [
                    CNC_PATH,
                    "init",
                    "solve",
                    path,
                    str(self.initial_divides),
                    str(self.online_divides),
                    str(self.initial_timeout),
                    str(self.timeout_factor),
                    str(int(self.future_mode)),
                ],
                check=True,
                cwd=working_dir,
            )
            eng = self.infra.split("-")[1]
            s = time()
            OUTFILE = "out"
            sub.run(
                [FORCE_PATH, "--jobs", str(self.jobs), "--engine", eng, OUTFILE],
                check=True,
                cwd=working_dir,
            )
            duration = time() - s
            o = open(join(working_dir, OUTFILE)).read().strip()
            assert len(o) < 20 and Runner.safe_str(o)
            result = o
            print(join(working_dir, ".gg"))
        else:
            print(f"Invalid infra: {self.infra}")
            exit(1)
        return CncOutput(result=result, duration=duration, family=family)


if __name__ == "__main__":
    main()
