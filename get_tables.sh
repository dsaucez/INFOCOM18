DIR=$1
ssh 10.0.2.2 -o port=41011 "sudo  ovs-ofctl -O OpenFlow13 dump-flows br-int" > $DIR>ovs1.table
ssh 10.0.2.2 -o port=41012 "sudo  ovs-ofctl -O OpenFlow13 dump-flows br-int" > $DIR>ovs2.table
