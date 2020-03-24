CNF=$1
numDivides=$2
rm -rf test
mkdir test
cd test
../splitter.sh ../../../march_cu/march_cu ../$CNF $numDivides test.cnf
for i in $(seq 0 $((2 **  $numDivides - 1)))
do
    ../solve.sh ../../../iglucose/core/iglucose ../$CNF test.cnf.$i out.test.$i
done
../merge.sh out.test $numDivides merge-output.test
if [[ $(cat merge-output.test) == "UNSAT" ]]
then
    echo "UNSAT, as expected"
    rm -rf test
else
    echo "SAT, not as expected"
    exit 1
fi
