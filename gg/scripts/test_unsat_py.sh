CNF=$1
numDivides=$2
rm -rf test
mkdir test
cd test
echo "a 0" > emptycnf
../splitter.py ../../../march_cu/march_cu ../$CNF emptycnf $numDivides
e=$((2 ** $numDivides - 1))
for i in $(seq 0 $e)
do
    ../solve.py ../../../iglucose/core/iglucose ../$CNF cube$i sub$i
done
../merge.py $numDivides $(for i in $(seq 0 $e); do echo sub$i; done)
if [[ $(cat out) == "UNSAT" ]]
then
    echo "UNSAT, as expected"
    rm -rf test
else
    echo "SAT, not as expected"
    exit 1
fi
