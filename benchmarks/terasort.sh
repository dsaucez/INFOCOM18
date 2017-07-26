XP=$1
sleep 42
ssh 10.0.2.2 -o port=45011 "killall python"
ssh 10.0.2.2 -o port=45011 "./start_noise.sh $XP"
echo "  Prepare input.."
echo `date +'%s.%N'`" Ben3.start"
hadoop jar $HADOOP_EXAMPLES teragen 10000000 /terasort-input
echo `date +'%s.%N'`" Ben3.stop"

sleep 42
ssh 10.0.2.2 -o port=45011 "killall python"
ssh 10.0.2.2 -o port=45011 "./start_noise.sh $XP"
echo "  Run TeraSort..."
echo `date +'%s.%N'`" Ben4.start"
hadoop jar $HADOOP_EXAMPLES terasort /terasort-input /terasort-output
echo `date +'%s.%N'`" Ben4.stop"
