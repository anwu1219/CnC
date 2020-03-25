#! /usr/bin/python3

import sys
import os
import subprocess

solverPath, CNF, cubeFile, outPath=sys.argv[1:]

print(sys.argv)

newCNF="temp.icnf"
with open(newCNF, 'w') as out_file:
    out_file.write("p inccnf\n")
    with open(CNF, 'r') as in_file:
        for line in in_file.readlines():
            if line[0] != 'c':
                out_file.write(line)
    with open(cubeFile, 'r') as in_file:
        for line in in_file.readlines():
            out_file.write(line)
output = subprocess.run([solverPath, newCNF], check=True, stdout=subprocess.PIPE)
output = output.stdout.decode()
print("\n\noutput:\n", output)
with open(outPath, 'w') as out_file:
    if "s UNSAT" in output:
        out_file.write("UNSAT\n")
    else:
        out_file.write("SAT\n")
os.remove(newCNF)
