#!/usr/bin/env python3
import sys
import subprocess
import os

marchPath, CNF, cube, numDivides = sys.argv[1:]
numDivides = int(numDivides)

def append_cube_as_cnf(cnf_path, cube_path, merged_path):
    """ Glues a CNF file and a cube file, creating a CNF file
    Assumes a single cube line.
    """
    with open(merged_path, "w") as out_file:
        cubeToWrite = ""
        numLitsinCube = 0  # Number of literals in the cube
        with open(cube_path, "r") as in_file:
            line = in_file.readlines()[0]
            for lit in line.split()[1:-1]:
                numLitsinCube += 1
                # Adding the literal as a clause
                cubeToWrite += f"{lit} 0\n"
        with open(cnf_path, "r") as in_file:
            for line in in_file.readlines():
                if line[0] == "p":
                    numClause = int(line.split()[-1])
                    out_file.write(
                        " ".join(line.split()[:-1]) + f" {numClause + numLitsinCube}\n"
                    )
                elif line[0] != "c":
                    out_file.write(line)
        out_file.write(cubeToWrite)

def append_cube_lines(cube_path, new_line, out_path):
    def parse_cube(s):
        ts = s.split()
        assert len(ts) >= 2, f"Cubes must have length >= 2, {s} does not"
        assert ts[0] == "a", f"Cubes must start with 'a', {s} does not"
        assert ts[-1] == "0", f"Cubes must end with '0', {s} does not"
        return ts[1:-1]
    def unparse_cube(xs):
        return "a " + " ".join(xs) + " 0"
    with open(out_path, "w") as f:
        with open(cube_path) as c:
            f.writelines([unparse_cube(parse_cube(c.read()) + parse_cube(new_line))])

temp = "merged.cnf.temp"
append_cube_as_cnf(CNF, cube, temp)

tempOut = "cubes"
subprocess.run([marchPath, temp, "-o", tempOut, "-l", str(2 ** numDivides)], check = True)

with open(tempOut, "r") as f:
    for i, l in enumerate(f.readlines()):
        append_cube_lines(cube, l, f"cube{i}")
os.remove(temp)
os.remove(tempOut)
