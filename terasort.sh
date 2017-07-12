sleep 42
echo "  Prepare input.."
hadoop jar $HADOOP_EXAMPLES teragen 10000000 /terasort-input

sleep 42
echo "  Run TeraSort..."
hadoop jar $HADOOP_EXAMPLES terasort /terasort-input /terasort-output
