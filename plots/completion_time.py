#!/usr/bin/python
import sys
import time
import datetime

def to_unix(d):
    return time.mktime(datetime.datetime.strptime(d, "%y/%m/%d %H:%M:%S").timetuple())

def get_time(line):
    tokens = line.split(" ")
    d = "%s %s" % (tokens[0], tokens[1])
    return d

start = -1                                                                                                                                                                                      
stop = -1

benchmark_number =1

for line in sys.stdin:
    line = line.strip()
    # == Put
    # start
    if line.find("Ben1.start") != -1:
        tokens = line.split(" ")
        start = float(tokens[0])
    # stop
    if line.find("Ben1.stop") != -1:
        tokens = line.split(" ")
        stop = float(tokens[0])
        print benchmark_number, " ",(stop-start)
        benchmark_number = benchmark_number + 1

    # == Normal Map reduce ===
    # start
    if line.find("INFO client.RMProxy: Connecting to ResourceManager") != -1:
        d = get_time(line)
        start = float(to_unix(d))
    # stop
    if line.find("completed successfully") != - 1:
        d = get_time(line)
        stop = float(to_unix(d))
        print benchmark_number, " ",(stop-start)
        benchmark_number = benchmark_number + 1
