#!/usr/bin/python
import sys
# <optimal source ports> <all source ports>

optimal_filter=sys.argv[1]
all_filter=sys.argv[2]

optimal_sports=dict()
all_sports=dict()

with open(optimal_filter) as f:
    for line in f:
        line = line.strip()
        optimal_sports[line] = True


with open(all_filter) as f:
    for line in f:
        line = line.strip()
        all_sports[line] = True


optimal_volume = 0.0
all_volume = 0.0
for line in sys.stdin:
    line = line.strip()
    (sport, cl, volume) = line.split()
    if sport in all_sports:
        all_volume = all_volume + int(volume)
    if sport in optimal_sports:
        optimal_volume = optimal_volume + int(volume)

print optimal_volume/all_volume
