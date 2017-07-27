import re
import sys

directory = sys.argv[1]
controller_file = "%s/controller.out" %(directory)


optimized_best_effort = dict()
load = dict()

with open(controller_file) as f:
    for line in f:
        m = re.search("(.*) optimize flow  (.*)_10010 on (.*) :  True"  , line)
        if m:
            flow = m.group(2)
            in_port = m.group(3)
            (src, dst, proto, sport) = flow.split("_")
            entry = "priority=42,tcp,in_port=%s,nw_src=%s,nw_dst=%s,tp_src=%s,tp_dst=10010" %(in_port, src, dst, sport)
#            print "[",entry,"]"
            optimized_best_effort[entry] = True

ovs_files = ["%s/ovs1.table.log" %(directory), "%s/ovs2.table.log" %(directory)]


total_bytes = 0

nb_packet_in = 0
for fname in ovs_files:
    with open(fname) as f:
        for line in f:
            tokens = line.split()
            if len(tokens) != 7:
                continue 
            entry = tokens[5]
            m = re.search("tp_src=(.*),tp_dst=(.*)$", entry)
            if entry in optimized_best_effort or (m and (m.group(1) != "10010" and m.group(2) != "10010") ):
                n_bytes= tokens[4]
                m = re.search("n_bytes=(.*),", n_bytes)
                n_bytes = int(m.group(1))
                total_bytes = total_bytes + n_bytes
                duration = tokens[1]
                m = re.search("duration=(.*)s", duration)
                duration = float(m.group(1))
                time = int(duration)
                count = load.setdefault(time, 0)
                count = count + 1
                load[time] = count
                nb_packet_in = nb_packet_in + 1
#                print tokens[1],"\t",m.group(1),"\t",entry
#             cookie=0x0, duration=63.953s, table=0, n_packets=7462, n_bytes=494742, priority=42,tcp,in_port=2,nw_src=192.0.2.2,nw_dst=192.0.2.4,tp_src=38896,tp_dst=13562 actions=output:4

max_load = 0
for (time, count) in load.items():
    if count > max_load:
        max_load = count

#print max_load #, nb_packet_in
print total_bytes











