CNF=$1
DIR=$2
cuber=$3
depth=$4

if [[ $CNF == "--help" ]]; then
    echo "usage: ./cube-lingeling.sh [CNF] [OUT_DIR] [march/louvain] [depth]"
    exit
fi

if [[ -d $DIR ]]; then
    echo "Directoy exists: $DIR"
    exit
fi

mkdir $DIR

if [[ $cuber == "march" ]]; then
    ./march_cu/march_cu $CNF -o $DIR/cubes -d $depth
else
    ./march_cu/march_cu $CNF -o $DIR/cubes $5 $6 $7 $8 $9
fi

echo "p inccnf" > $DIR/formula.icnf
cat $CNF | grep -v c >> $DIR/formula.icnf
cat $DIR/cubes >> $DIR/formula.icnf
time ./lingeling/ilingeling $DIR/formula.icnf -b 8
rm $DIR/formula.icnf
