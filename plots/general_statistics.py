#!/usr/bin/python
# files
from os import listdir
from os.path import isfile, isdir, join

# statistics
import numpy as np
import scipy.stats as st
import matplotlib.pyplot as plt

# returns confidence interval
# return (low conf, mean, high conf)
def conf_interval(durations, confidence):
    array = 1.0*np.array(durations)
    mean = np.mean(array)
    (minconf, maxconf) =  st.t.interval(confidence, len(array)-1, loc=mean, scale=st.sem(array))
    return (mean-minconf, mean, maxconf-mean)



#a = [10,12,10,11,9,10.0001]
#(low,mean,high) = conf_interval(a, 0.95)
#yerr = [mean-low]
#x = [1]
#y=[10.0]
#print x
#print y
#print yerr
#plt.errorbar(x,y, yerr=yerr, label='random')
#plt.show()
#exit()


def extract_parameters(str):
    import re
    groups = re.search("c_(.*)__random_(.*)", str)
    c = float(groups.group(1))
    r = int(groups.group(2))
    return (c, r)

datapath = "data"

# get all experiments
xps = [d for d in listdir(datapath) if isdir(join(datapath, d))]

a = np.empty(shape=[0,6])
# get all runs for each experiment
for xp in xps:
    data = dict()
    duration_file = join(datapath, xp, "durations.log")
    with open(duration_file) as f:
        for line in f:
            line = line.strip()
            (benchmark, duration) = line.split()
            benchmark = float(benchmark)
            duration = float(duration)
            
            lst = data.setdefault(benchmark, list())
            lst.append(duration)
            data[benchmark] = lst
    (c, r) = extract_parameters(xp)
    for (bench,v) in data.items():
        (low, mean, high) = conf_interval(v, 0.95)
        a = np.vstack((a, np.array([bench, c, r, low, mean, high])))

x = [0.01, 0.1, 0.3, 0.7, 0.9]

titles=["put", "wordcount", "teragen", "terasort"]

print a

for bench in range(1,5):
    plt.cla()
    print bench
    b = a[:,0]
    condition = b == bench
    bench_a = a[condition]
    b = bench_a[:,2]
    condition = b == 1.0
    rand_bench_a = bench_a[condition]
    condition = b == 0.0
    stochapp_bench_a = bench_a[condition]


    y = stochapp_bench_a[:,4]
    yerr = stochapp_bench_a[:,5]
    plt.errorbar(x,y, yerr=yerr, label='STOCHAPP')

    y = rand_bench_a[:,4]
    yerr = rand_bench_a[:,5]
    plt.errorbar(x,y, yerr=yerr, label='random')
    
    axes = plt.gca()
    axes.set_xlim([0.009,1])

    plt.xscale('log')
    plt.xlabel('c')
    plt.ylabel('completion time')

    plt.legend(loc=3)
    plt.title(titles[bench-1])
    plt.savefig("figs/completion_time/%s.eps" % (titles[bench-1]))

