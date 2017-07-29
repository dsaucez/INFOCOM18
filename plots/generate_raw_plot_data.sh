for d in `ls data.wordcount`; do echo $d; cat data.wordcount/$d/flow_background_fraction.dat; done > raw_plot/flow_background_fraction.dat
for d in `ls data.wordcount`; do echo $d; cat data.wordcount/$d/flow_background_volume_fraction.dat; done > raw_plot/flow_background_volume_fraction.dat
for d in `ls data.wordcount`; do echo $d; cat data.wordcount/$d/maximum_controller_load.dat; done > raw_plot/maximum_controller_load.dat 
for d in `ls data.wordcount`; do echo $d; cat data.wordcount/$d/completion_time.dat | awk '{print $2}' | ./stats.py; done > raw_plot/completion_time.wordcount.dat 
for d in `ls data.terasort`;  do echo $d; cat data.terasort/$d/completion_time.dat | awk '{print $2}' | ./stats.py; done > raw_plot/completion_time.terasort.dat

vim raw_plot/flow_background_fraction.dat
vim raw_plot/flow_background_volume_fraction.dat
vim raw_plot/maximum_controller_load.dat 
vim raw_plot/completion_time.wordcount.dat 
vim raw_plot/completion_time.terasort.dat
