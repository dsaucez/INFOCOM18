echo "  Create directory..."
hadoop fs -mkdir -p /benchmarks/wordcount/input

./lorem.pl  100000 > $$
sleep 42
echo "  Create files..."
for i in {100..200}
do
   echo "    file$i"
#   ./lorem.pl  100000 > file$i
   hadoop fs -put $$ /benchmarks/wordcount/input/file$i
#   rm file$i
done
rm $$

sleep 42
echo "  Run wordcount..."

hadoop jar $HADOOP_EXAMPLES wordcount /benchmarks/wordcount/input /benchmarks/wordcount/output
