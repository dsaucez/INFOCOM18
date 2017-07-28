#!/usr/bin/python
import sys

flt=sys.argv[1]

values=dict()
with open(flt) as f:
    for line in f:
        line = line.strip()
        values[line] = True

for line in sys.stdin:
    line = line.strip()
    (key, data) = line.split()
    if key in values:
        print data
