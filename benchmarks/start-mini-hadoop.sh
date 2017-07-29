#!/bin/bash
echo "== Copy predictor"
scp -o port=41001 flow.dat 10.0.2.2:
scp -o port=45011 flow.dat 10.0.2.2: 
scp -o port=45012 flow.dat 10.0.2.2:

echo "== prepare network"
ssh 10.0.2.2 -o port=41001 "killall ryu-manager"
ssh 10.0.2.2 -o port=41001 "./start_controller.sh 0.999 1 0"
ssh 10.0.2.2 -o port=41011 "./reset_switch.sh"
ssh 10.0.2.2 -o port=41012 "./reset_switch.sh"
ssh 10.0.2.2 -o port=45011 "killall python"
ssh 10.0.2.2 -o port=45011 "rm noise.err noise.out"
ssh 10.0.2.2 -o port=45012 "killall python"
echo "done"
sleep 10


echo "== Stop hadoop"
./stop-hadoop.sh
echo "done"

echo "== prepare HDFS"
echo "delete eveything"
rm -rf $HADOOP_HOME/hadoop2_data
rm -rf $HADOOP_HOME/logs/*

for s in 2 4 5
do
    echo "reset hadoop$s"
    ssh hadoop$s "rm -rf $HADOOP_HOME/hadoop2_data"
    ssh hadoop$s "rm -rf $HADOOP_HOME/logs/*"
done

echo "create direcotries"
mkdir -p $HADOOP_HOME/hadoop2_data/hdfs/namenode
mkdir -p $HADOOP_HOME/hadoop2_data/hdfs/datanode

echo "format HDFS"
hadoop dfsadmin -safemode leave
hadoop namenode -format
echo "done"

echo "== Start hadoop"
$HADOOP_HOME/sbin/start-dfs.sh
$HADOOP_HOME/sbin/start-yarn.sh
echo "done"


####echo "== create wordcount directory..."
####hadoop fs -mkdir -p /benchmarks/wordcount/input
####sleep 42
####echo "done"
####
####echo "== Create lorem ipsum files..."
####for i in {100..200}
####do
####    echo "  file$i"
####    ./lorem.pl  100000 $i > $$
####    hadoop fs -put $$ /benchmarks/wordcount/input/file$i
####    rm $$
####done
####echo "done"

##############################################################
echo "== Create terasort data (teragen)"
#hadoop dfsadmin -safemode leave
hadoop fs -rm -r -f -skipTrash /terasort-input
hadoop jar $HADOOP_EXAMPLES teragen 10000000 /terasort-input
sleep 42
echo "done"
###############################################################


for XP in 1 2 3 # 4 5 6 7 8 9 10 #11 12 13 14 15
do
    for ryu_c in 0.3 #0.7 0.1 0.9
    do
        for ryu_random in 2 # 0 1 2
        do
            d=`date +'%Y%m%d_%H%M%S.%N'`
            LOG_DIR=logs/c_${ryu_c}__random_${ryu_random}/$d
            mkdir -p $LOG_DIR
    
    
            echo "Run $XP logged in $LOG_DIR"
            echo "================================================="
            echo ""
    
            echo "== Restart controller and switches"
            ssh 10.0.2.2 -o port=41001 "killall ryu-manager"
            sleep 5
            ssh 10.0.2.2 -o port=41001 "./start_controller.sh ${ryu_c} ${ryu_random} ${XP}" 
            sleep 10
            ssh 10.0.2.2 -o port=41011 "./reset_switch.sh"
            ssh 10.0.2.2 -o port=41012 "./reset_switch.sh"
            sleep 10
            echo "done"
    
            echo "== Start noise"
            ssh 10.0.2.2 -o port=45012 "./servers.sh"
            sleep 10
            ssh 10.0.2.2 -o port=45011 "./start_noise.sh $XP"
            sleep 1
            echo "done"
    
####            ./mini-wordcount.sh 2>&1 | tee $LOG_DIR/wordcount.log
             ./mini-terasort.sh 2>&1 | tee $LOG_DIR/terasort.log
    
            echo "== Kill noise to flush tables"
            ssh 10.0.2.2 -o port=45011 "killall python"
            sleep 2
            ssh 10.0.2.2 -o port=45012 "killall python"
            sleep 20
            echo "...wait 180s!!!"
            sleep 180
            echo "done"
    
            echo "== Get table logs"
            ssh 10.0.2.2 -o port=41011 "sudo  ovs-ofctl -O OpenFlow13 dump-flows br-int" > $LOG_DIR/ovs1.table.log
            ssh 10.0.2.2 -o port=41012 "sudo  ovs-ofctl -O OpenFlow13 dump-flows br-int" > $LOG_DIR/ovs2.table.log
            echo "done"
    
            echo "== Get logs"
            scp -o port=41001 10.0.2.2:controller.out 10.0.2.2:controller.err $LOG_DIR/
            scp -o port=45011 10.0.2.2:noise.out 10.0.2.2:noise.err $LOG_DIR/
            echo "done"
    
            echo "== clean HDFS"
####            hadoop fs -rm -r -f -skipTrash /benchmarks/wordcount/output
            hadoop fs -rm -r -f -skipTrash /terasort-output
            echo "done"
        done
    done
done

echo "== Stop hadoop"
./stop-hadoop.sh
echo "done"

echo "== Stop network"
ssh 10.0.2.2 -o port=41001 "killall ryu-manager"
echo "done"
