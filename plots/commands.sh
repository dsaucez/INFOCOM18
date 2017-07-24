# completion_time
rm data/*/completion_time.log
for e in `ls data`
do 
  echo "$e";
  for f in `ls data/$e | grep "^2017"`
    do
      dir="data/$e/$f"
      cat $dir/wordcount.log $dir/terasort.log |./completion_time.py
    done > /tmp/completion_time.log
    mv /tmp/completion_time.log data/$e/completion_time.log

    cat  data/$e/*/noise.out | grep "Mbps"| awk '{print $2}' | ./stats.py > data/$e/noise.dat
done
./statistics.py
