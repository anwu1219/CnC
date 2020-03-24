inputPrefix=$1
numDivides=$2
output=$3

for i in $(seq 0 $((2 ** $numDivides -1)))
do
    UNSAT=`cat $inputPrefix.$i | grep "UNSAT" | wc |awk '{print $1}'`
    if [[ $UNSAT == 0 ]]
    then
        echo "SAT" > $output
        exit
    fi
done
echo "UNSAT" > $output
