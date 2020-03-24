./splitter.sh march_cu/march_cu tests/random_ksat.dimacs 2 test.cnf
for i in {0..3}
do
    ./solve.sh iglucose/core/iglucose tests/random_ksat.dimacs test.cnf.$i out.test.$i
done
./merge.sh out.test 2 merge-output.test
if [[ $(cat merge-output.test) == "UNSAT" ]]
then
    echo "UNSAT"
else
    exit 1
fi
