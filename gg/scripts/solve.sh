solverPath=$1
CNF=$2
cubeFile=$3
outPath=$4

newCNF=$CNF.$cubeFile
echo "p inccnf" > $newCNF
cat $CNF | grep -v c >> $newCNF
cat $cubeFile >> $newCNF
$solverPath $newCNF | egrep -o "s UNSAT|s SAT" > $outPath
rm $newCNF
