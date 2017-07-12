#!/bin/bash

# == prepare HDFS
# delete eveything
rm -rf $HADOOP_HOME/hadoop2_data

for s in {2..5}
do
  ssh hadoop$s "rm -rf $HADOOP_HOME/hadoop2_data"
done

# create direcotries
mkdir -p $HADOOP_HOME/hadoop2_data/hdfs/namenode
mkdir -p $HADOOP_HOME/hadoop2_data/hdfs/datanode

# format HDFS
hadoop namenode -format

# == Start hadoop
$HADOOP_HOME/sbin/start-dfs.sh
$HADOOP_HOME/sbin/start-yarn.sh

sleep 10
# == Start the benchmarks
./benchmarks.sh

