LOG_DIR=$1
XP=$2
mkdir -p $LOG_DIR
echo "Wordcount benchmark"
./wordcount.sh $XP 2>&1 | tee $LOG_DIR/wordcount.log

echo "TeraSort"
./terasort.sh $XP 2>&1 | tee $LOG_DIR/terasort.log
