for e in `ls data/`
do
    echo $e
    for f in `ls data/$e | grep 2017`
    do
        dir="data/$e/$f"
        optimal=`cat $dir/controller.out  | grep "_10010 on 3" | grep "force"  | awk '{print $4}' | tr "_" " " | awk '{s++} END{print s}'`
        total=`cat $dir/controller.out    | grep "_10010 on 3" | grep "from the edge" |  awk '{print $3}' | tr "_" " " | awk '{s++} END{print s}'`
        echo "" | awk -v total=$total optimal=$optimal'{print optimal/total}'
    done | ./stats.py > data/$e/flow_background_fraction.dat

    for f in `ls data/$e | grep 2017`
    do
      dir="data/$e/$f"
      # optimal
      cat $dir/controller.out  | grep "_10010 on 3" | grep "force"  | awk '{print $4}' | tr "_" " " | awk '{print $4}' > $$.sport.optimal
      # all background
      cat $dir/controller.out | grep "_10010 on 3" | grep "from the edge" |  awk '{print $3}' | tr "_" " " | awk '{print $4}' > $$.sport.all
      cat ../flow.dat | ./compute_expected_fraction_optimal_volume.py $$.sport.optimal $$.sport.all
      rm $$.*
    done  | ./stats.py  > data/$e/flow_background_volume_fraction.dat
done
