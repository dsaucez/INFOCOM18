for e in `ls data/`
do
    echo $e
    for f in `ls data/$e | grep 2017`
    do
        dir="data/$e/$f"
        cat $dir/controller.err| grep "tcp_dst': 10010"| grep "in_port': 3" | awk '{print $8, $9,$13}' | tr "=" " " |  grep -v "duration_sec 180"  | awk '{print $2,$4,$NF}' | awk '{printf("%.4f\n", (($3*8)/((($1+($2/1000000000.0))-180.0))))}'
    done  > data/$e/backround_bw.dat
done
