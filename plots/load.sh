for e in `ls data/`
do
    echo $e
    for f in `ls data/$e | grep 2017`
    do
        dir="data/$e/$f"
        cat $dir/controller.out | grep "optimize" | grep "True$" | awk '{print int($1)}' | sort -n  | uniq -c| awk '{print $1}' | sort -n | tail -1
    done | ./stats.py > data/$e/maximum_controller_load.dat
done
