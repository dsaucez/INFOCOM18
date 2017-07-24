#!/usr/bin/python                                                                                                                                                    
# 
import sys
# statistics
import numpy as np
import scipy.stats as st
import matplotlib.pyplot as plt

# returns confidence interval
# return (low conf, mean, high conf)
def conf_interval(v, confidence):
    array = 1.0*np.array(v)
    mean = np.mean(array)
    (minconf, maxconf) =  st.t.interval(confidence, len(array)-1, loc=mean, scale=st.sem(array))
    return (minconf, mean, maxconf)

data = list()
for line in sys.stdin:
    data.append(float(line.strip()))

print " ".join([str(x) for x in conf_interval(data, 0.95)])
