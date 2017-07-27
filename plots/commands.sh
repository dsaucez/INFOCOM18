# completion_time
mkdir -p figs/completion_time
mkdir -p figs/noise
mkdir -p figs/load

rm data/*/completion_time.dat
rm data/*/noise.dat
rm data/*/max_load.dat

for e in `ls data`
do 
  echo "$e";
  for f in `ls data/$e | grep "^2017"`
    do
      dir="data/$e/$f"
      cat $dir/wordcount.log $dir/terasort.log |./completion_time.py
    done > /tmp/completion_time.dat
    mv /tmp/completion_time.dat data/$e/completion_time.dat

    cat  data/$e/*/noise.out | grep "Mbps"| awk '{print $2}' | ./stats.py > data/$e/noise.dat
    
      
    for f in `ls data/$e | grep "^2017"`
    do
      python load.py "data/$e/$f"
    done | ./stats.py  > data/$e/max_load.dat
done
./statistics.py
