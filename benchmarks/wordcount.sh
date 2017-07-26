XP=$1
echo "  Create directory..."
hadoop fs -mkdir -p /benchmarks/wordcount/input

./lorem.pl  100000 $XP > $$
sleep 42

ssh 10.0.2.2 -o port=45011 "killall python"
ssh 10.0.2.2 -o port=45011 "./start_noise.sh $XP"

echo "  Create files..."
echo `date +'%s.%N'`" Ben1.start"
for i in {100..200}
do
   echo "    file$i"
   hadoop fs -put $$ /benchmarks/wordcount/input/file$i
done
echo `date +'%s.%N'`" Ben1.stop"
rm $$

sleep 42
ssh 10.0.2.2 -o port=45011 "killall python"
ssh 10.0.2.2 -o port=45011 "./start_noise.sh $XP"
echo "  Run wordcount..."
echo `date +'%s.%N'`" Ben2.start"
hadoop jar $HADOOP_EXAMPLES wordcount /benchmarks/wordcount/input /benchmarks/wordcount/output
echo `date +'%s.%N'`" Ben2.stop"

