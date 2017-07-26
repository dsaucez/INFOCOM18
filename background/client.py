from multiprocessing import Pool
import time
import os

import socket
import sys

import numpy as np


# ===================================

def send_flow(sport, size, s_class):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    dport = 10010
    BUFSIZE = 1024

    try:
        server = ("Gen2", dport)
        sock.bind(("", sport))
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

_seed=int(sys.argv[1])
np.random.seed(_seed)

nb_classes = 3

print "seed:", _seed

pool = Pool(processes=100)
rate = 3

def chunks(total):
    BUFF_SIZE = 1024
    while total > 0:
        c = min(1024, total)
        print c
        total = total - c


with open("flow.dat") as f:
    for line in f:
        line = line.strip()
        (sport, size_class, size) = line.split()
        sport = int(sport)
        size_class = int(size_class)
        size = int (size)
        res = pool.apply_async(send_flow, (sport, size, size_class,))

        s_time = np.random.poisson(int(1.0/rate*1000))
        time.sleep(s_time/1000.0)
