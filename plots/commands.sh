# completion_time
mkdir -p figs/completion_time
mkdir -p figs/noise
mkdir -p figs/load

rm data/*/*.dat
for e in `ls data`
do 
  echo "$e";
  for f in `ls data/$e | grep "^2017"`
    do
      dir="data/$e/$f"
#      cat $dir/wordcount.log $dir/terasort.log |./completion_time.py
       cat $dir/terasort.log | ./completion_time.py
#      cat $dir/wordcount.log | ./completion_time.py
    done > /tmp/completion_time.dat
    mv /tmp/completion_time.dat data/$e/completion_time.dat
done


sh flow_background_fraction.sh
sh load.sh

./statistics.py
