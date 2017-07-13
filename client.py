from multiprocessing import Pool, TimeoutError
import time
import os

import socket
import sys

import numpy as np

from numpy.lib.scimath import logn
from math import e

# =======================
def build_classes(avg, nb_classes):
    limits = list()
    step = 100/nb_classes
    for c in range(step,100/nb_classes*nb_classes, step):
        limits.append(-logn(e, (100.0-c)/100.0)*avg)
    return limits


def what_class(v):
    curr_class = len(limits)+1
    for l in limits:
        if v < l:
            break
        else:
            curr_class = curr_class - 1
    return curr_class

# ===================================

def f(port, size):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s_class = what_class(size)
    port = port + s_class
    BUFSIZE = 1024

    try:
        server = ("Gen2", port)
        sock.connect(server)
        start = time.time()
        remaining = size
        while remaining > 0:
            c = min(BUFSIZE, remaining)
            message = "1" * c
            sock.sendall(message)
            remaining = remaining - c
        stop = time.time()
        print "Speed: ", ((size * 8.0)/(stop-start)/1000/1000), "Mbps"
    except Exception as e:
        print e
    finally:
        sock.close()

    return True



avg = 10*1024
nb_classes = 3

limits = build_classes(avg, nb_classes)

print limits

pool = Pool(processes=10)
rate = 10

def chunks(total):
    BUFF_SIZE = 1024
    while total > 0:
        c = min(1024, total)
        print c
        total = total - c

i = 0
while True:
    i = i + 1
    s_size = int(np.random.exponential(avg))
    s_time = np.random.poisson(int(1.0/rate*1000))

    res = pool.apply_async(f, (10010, s_size,))
    time.sleep(s_time/1000.0)
