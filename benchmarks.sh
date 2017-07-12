LOG_DIR=logs/`date +'%Y%m%d_%H%M%S.%N'`
mkdir -p $LOG_DIR
echo "Wordcount benchmark"
./wordcount.sh 2>&1 | tee $LOG_DIR/wordcount.log

#echo "TeraSort"
./terasort.sh 2>&1 | tee $LOG_DIR/terasort.log
