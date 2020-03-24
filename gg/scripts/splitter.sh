marchPath=$1
CNF=$2
numDivides=$3
outPrefix=$4

$marchPath $CNF -o $outPrefix -l $((2 ** $numDivides))

for i in $(seq 0 $((2 ** $numDivides - 1)))
do
    cat $outPrefix | head -n $((i + 1)) | tail -n 1 > $outPrefix.$i
done
