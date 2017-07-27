echo "== Run wordcount..."
hadoop jar $HADOOP_EXAMPLES wordcount /benchmarks/wordcount/input /benchmarks/wordcount/output
echo "done"
