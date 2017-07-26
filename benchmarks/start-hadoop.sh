#!/bin/bash
# parameters
ryu_c="$1"
ryu_random="$2"

for i in {1..5}
do
        XP=$i
        d=`date +'%Y%m%d_%H%M%S.%N'`
	LOG_DIR=logs/c_${ryu_c}__random_${ryu_random}/$d

	echo "Run $XP logged in $LOG_DIR"
	echo ""
        mkdir -p $LOG_DIR

	echo "prepare nework"
	ssh 10.0.2.2 -o port=41001 "killall ryu-manager"
	ssh 10.0.2.2 -o port=41001 "./start_controller.sh ${ryu_c} ${ryu_random} ${XP}"
	ssh 10.0.2.2 -o port=41011 "./reset_switch.sh"
	ssh 10.0.2.2 -o port=41012 "./reset_switch.sh"
        ssh 10.0.2.2 -o port=45011 "killall python"
        ssh 10.0.2.2 -o port=45011 "rm noise.err noise.out"
        ssh 10.0.2.2 -o port=45012 "killall python"
        echo "done"
	sleep 10

	echo "== prepare HDFS"
	echo "delete eveything"
	rm -rf $HADOOP_HOME/hadoop2_data

	for s in 2 4 5
	do
	  echo "reset hadoop$s"
	  ssh hadoop$s "rm -rf $HADOOP_HOME/hadoop2_data"
	done

	echo "create direcotries"
	mkdir -p $HADOOP_HOME/hadoop2_data/hdfs/namenode
	mkdir -p $HADOOP_HOME/hadoop2_data/hdfs/datanode

	echo "format HDFS"
	hadoop namenode -format
        echo "done"

	echo "== Start hadoop"
	$HADOOP_HOME/sbin/start-dfs.sh
	$HADOOP_HOME/sbin/start-yarn.sh
        echo "done"

        sleep 10
        echo "== Start noise"
        ssh 10.0.2.2 -o port=45012 "./servers.sh"
        sleep 5
        echo "done"

	sleep 10
	echo "== Start the benchmarks"
	./benchmarks.sh $LOG_DIR $XP
        echo "done"


	echo "== get table logs"
	ssh 10.0.2.2 -o port=41011 "sudo  ovs-ofctl -O OpenFlow13 dump-flows br-int" > $LOG_DIR/ovs1.table.log
	ssh 10.0.2.2 -o port=41012 "sudo  ovs-ofctl -O OpenFlow13 dump-flows br-int" > $LOG_DIR/ovs2.table.log
        echo "done"

	echo "== Stop hadoop"
	./stop-hadoop.sh
        echo "done"

	echo "== Stop network"
        ssh 10.0.2.2 -o port=45011 "killall python"
        ssh 10.0.2.2 -o port=45012 "killall python"
	ssh 10.0.2.2 -o port=41001 "killall ryu-manager"
        echo "done"
        sleep 5

	echo "== Get logs"
	scp -o port=41001 10.0.2.2:controller.out 10.0.2.2:controller.err $LOG_DIR/
	scp -o port=45011 10.0.2.2:noise.out 10.0.2.2:noise.err $LOG_DIR/
        echo "done"
        sleep 60
done
