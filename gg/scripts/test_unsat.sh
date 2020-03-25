CNF=$1
numDivides=$2
rm -rf test
mkdir test
cd test
../splitter.sh ../../../march_cu/march_cu ../$CNF $numDivides test.cnf
e=$((2 ** $numDivides - 1))
for i in $(seq 0 $e)
do
    ../solve.sh ../../../iglucose/core/iglucose ../$CNF test.cnf.$i out.test.$i
done
../merge.sh $numDivides merge-output.test $(for i in $(seq 0 $e); do echo out.test.$i; done)
if [[ $(cat merge-output.test) == "UNSAT" ]]
then
    echo "UNSAT, as expected"
    rm -rf test
else
    echo "SAT, not as expected"
    exit 1
fi
