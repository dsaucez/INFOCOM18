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
def conf_interval(completion_times, confidence):
    array = 1.0*np.array(completion_times)
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
fraction = dict()
noise = dict()
load = dict()

# get all runs for each experiment
for xp in xps:
    (c, r) = extract_parameters(xp)

    # completion time
    data = dict()
    completion_time_file = join(datapath, xp, "completion_time.dat")
    with open(completion_time_file) as f:
        for line in f:
            line = line.strip()
            (benchmark, completion_time) = line.split()
            benchmark = float(benchmark)
            completion_time = float(completion_time)
            
            lst = data.setdefault(benchmark, list())
            lst.append(completion_time)
            data[benchmark] = lst
    for (bench,v) in data.items():
        (low, mean, high) = conf_interval(v, 0.95)
        a = np.vstack((a, np.array([bench, c, r, low, mean, high])))


    if True:
        # fraction
        fraction_file = join(datapath, xp, "optimized_fraction.dat")
        with open(fraction_file) as f:
            for line in f:
                line = line.strip()
                (low,mean,high) = (float(v) for v in line.split())
                _c = fraction.setdefault(c, dict())
                _r = _c.setdefault(r, dict())
                fraction[c][r]["low"]  = mean-low
                fraction[c][r]["mean"] = mean
                fraction[c][r]["high"] = high-mean

        print "fraction:"
        print fraction



    if False:
        # noise
        noise_file = join(datapath, xp, "noise.dat")
        with open(noise_file) as f:
            for line in f:
                line = line.strip()
                (low,mean,high) = (float(v) for v in line.split())
                _c = noise.setdefault(c, dict())
                _r = _c.setdefault(r, dict())
                noise[c][r]["low"]  = mean-low
                noise[c][r]["mean"] = mean
                noise[c][r]["high"] = high-mean

        print "noise:"
        print noise

    if False:
        # load
        load_file = join(datapath, xp, "max_load.dat")
        with open(load_file) as f:
            for line in f:
                line = line.strip()
                (low,mean,high) = (float(v) for v in line.split())
                _c = load.setdefault(c, dict())
                _r = _c.setdefault(r, dict())
                load[c][r]["low"]  = mean-low
                load[c][r]["mean"] = mean
                load[c][r]["high"] = high-mean
        print "load:"
        print load


x = [0.01, 0.1, 0.3, 0.7, 0.9]
x = [0.3, 0.7]

titles=["put", "wordcount", "teragen", "terasort"]
titles=["wordcount"]

print a

# plot completion time
for bench in range(1,2): #5):
    plt.cla()
    print "\t\t!!!!",bench

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
    plt.errorbar(x,y, yerr=yerr, label='SOFIA')

    y = rand_bench_a[:,4]
    yerr = rand_bench_a[:,5]
    plt.errorbar(x,y, yerr=yerr, label='random')
    
    axes = plt.gca()
    axes.set_xlim([0,1])
    plt.ylim(ymin=0.0)

###    plt.xscale('log')
    plt.xlabel('c')
    plt.ylabel('completion time [s]')

    plt.legend(loc=3)
###    plt.title(titles[bench-1])
    plt.savefig("figs/completion_time/completion_time_%s.eps" % (titles[bench-1]))


if True:
    # plot fraction

    x = list()
    
    y = list()
    yerr = list()

    y_rand = list()
    yerr_rand = list()

    for c in fraction.keys():
        x.append(c)
        y.append(fraction[c][0]["mean"])
        yerr.append(fraction[c][0]["low"])

        y_rand.append(fraction[c][1]["mean"])
        yerr_rand.append(fraction[c][1]["low"])

    plt.cla()
    plt.errorbar(x, y, yerr=yerr, label='SOFIA')
    axes = plt.gca()
    axes.set_xlim([0,1])
    plt.ylim(ymin=0.0)


    plt.errorbar(x, y_rand, yerr=yerr_rand, label='random')

#    plt.xscale('log')
    plt.xlabel('c')
    plt.ylabel('Fraction of traffic')
    plt.legend(loc=3)

    plt.savefig("figs/noise/optimized_volume.eps")



if False:
    # plot noise
    x = list()

    y = list()
    yerr = list()

    y_rand = list()
    yerr_rand = list()

    for c in noise.keys():
        x.append(c)
        y.append(noise[c][0]["mean"])
        yerr.append(noise[c][0]["low"])

        y_rand.append(noise[c][1]["mean"])
        yerr_rand.append(noise[c][1]["low"])

    plt.cla()
    plt.errorbar(x, y, yerr=yerr, label='SOFIA')
    axes = plt.gca()
    axes.set_xlim([0,1])
    plt.ylim(ymin=0.0)


    plt.errorbar(x, y_rand, yerr=yerr_rand, label='random')

#    plt.xscale('log')
    plt.xlabel('c')
    plt.ylabel('background traffic [Mbps]')
    plt.legend(loc=3)

    plt.savefig("figs/noise/background_bandwidth.eps")


if False:
    # plot load
    
    x = list()

    y = list()
    yerr = list()

    y_rand = list()
    yerr_rand = list()
    for c in load.keys():
        x.append(c)

        y.append(load[c][0]["mean"])
        yerr.append(load[c][0]["low"])

        y_rand.append(load[c][1]["mean"])
        yerr_rand.append(load[c][1]["low"])

    plt.cla()
    plt.errorbar(x, y, yerr=yerr, label='SOFIA')
    axes = plt.gca()
    axes.set_xlim([0,1])
    plt.ylim(ymin=0.0)

    plt.errorbar(x, y_rand, yerr=yerr_rand, label='random')

    plt.xscale('log')
    plt.xlabel('c')
    plt.ylabel('optimized volume [bytes]')
    #plt.ylabel('maximum load [packet_in / sec]')
    plt.legend(loc=3)

    plt.savefig("figs/load/optimized_volume.eps")
    #plt.savefig("figs/load/max_load.eps")


