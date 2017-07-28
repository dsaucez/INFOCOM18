for e in `ls data/`
do
    echo $e
    for f in `ls data/$e | grep 2017`
    do
        dir="data/$e/$f"
        total=`cat $dir/controller.err | grep "priority="| grep "tcp_dst': 10010"| grep "in_port': 3" | awk '{print $13}' | tr "=" " " | awk '{s+=$2;c++} END {printf("%.1f\n", s)}' `
        optimal=`cat $dir/controller.err | grep "priority=69"| grep "tcp_dst': 10010"| grep "in_port': 3" | awk '{print $13}' | tr "=" " " | awk '{s+=$2;c++} END {printf("%.1f\n", s)}' `
        echo "" | awk -v total=$total optimal=$optimal'{print optimal/total}'
    done | ./stats.py  > data/$e/flow_background_volume.dat
done
