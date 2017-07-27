# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


###### monitoring taken from https://github.com/muzixing/ryu/blob/master/ryu/app/simple_monitor.py

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import in_proto as inet
from ryu.lib.packet import tcp
from ryu.lib.packet import udp


from operator import attrgetter

# ====
from random import seed
from random import random
from time import time
import os

class Flow:
    def __init__(self, src=None, dst=None, proto=None, in_port=None, predictor=None):
        self.src = src
        self.dst = dst
        self.proto = proto
        self.sport = None
        self.dport = None
        self.predictor = predictor
        self.in_port = in_port

    # == Size predictor
    def size_class(self):
        assert(self.is_best_effort())
        assert(self.sport in self.predictor)
        return self.predictor[self.sport]

    def is_best_effort(self):
         return (self.proto == 6 and self.dport == 10010)

    # == tuple matching
    def _matchTCP(self, parser):
        """
        Returns a match for a TCP flow
        """
        match = parser.OFPMatch(in_port=self.in_port, eth_type=0x0800, ipv4_src=self.src, ipv4_dst=self.dst, ip_proto=6, tcp_src=self.sport, tcp_dst=self.dport)
        return match

    def _matchUDP(self, parser):
        """
        Returns a match for a UDP flow
        """
        match = parser.OFPMatch(in_port=self.in_port, eth_type=0x0800, ipv4_src=self.src, ipv4_dst=self.dst, ip_proto=17, udp_src=self.sport, udp_dst=self.dport)
        return match

    def _matchICMP(self, parser):
        """
        Returns a match for an ICMP flow
        """
        match = parser.OFPMatch(in_port=self.in_port, eth_type=0x0800, ipv4_src=self.src, ipv4_dst=self.dst, ip_proto=1)
        return match

    def match(self, parser):
        """
        Returns an OpenFlow match for the flow
        """
        # TCP?
        if self.proto == 6:
           return self._matchTCP(parser)
        # UDP?
        elif self.proto == 17:
           return self._matchUDP(parser)
        # ICMP?
        elif self.proto == 1:
           return self._matchICMP(parser)
        else:
           raise Exception("Unsupported protocol")

    # == Miscelaneous
    def __str__(self):
        value = "%s_%s_%d_%s_%s on %s" % (self.src, self.dst, self.proto, str(self.sport), str(self.dport), str(self.in_port))
        return value

    def __hash__(self):
        return self.__str__().__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


class ExampleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ExampleSwitch13, self).__init__(*args, **kwargs)
        # initialize mac address table.
        self.mac_to_port = {}
       
        # == flows ===========================================================
        # Number of flow classes
        self.NB_CLASSES = 1000

        # Last time the threshold has been recomputed
        self.last_update = 0.0

        # Interval between two threshold recomputations (in seconds, float)
        self.T = 60.0

        # Average load on the controller (c \in \left[0; 1\right])
        self.c = 0.5
        if "ryu_c" in os.environ:
           self.c = float( os.environ["ryu_c"])
        # are we using random instead of STOCHAPP?
        self.random=False
        if "ryu_random" in os.environ:
           self.random = bool( int(os.environ["ryu_random"]))
        # seed for the experiement
        self.seed = 0
        if "ryu_XP" in os.environ:
           self.seed = int(os.environ["ryu_XP"])
        seed(int(self.seed))

        # Current alpha value
        self.alpha = (self.NB_CLASSES / 2.0)
        converged_alpha = {0.9:998.0, 0.7:998.0,0.5:991.0,0.3:946.0,0.1:650.0,0.01:113.0}
        if self.c in converged_alpha:
            self.alpha = converged_alpha[self.c]

        # STOCHAPP Convergence parameter (epsilon \in \left[0; 1\right])
        self.epsilon = 10.0

        # Statistics on the number of observations for flow classes
	#     observations_classes[0] = total number of observations
        #     observations_classes[i>0] = number of observations for class i
        self.observations_classes = list()#[0, 0, 0, 0]
        for i in range(0, self.NB_CLASSES + 1):
            self.observations_classes.append(0)

	# Statistics of the number of accepted and rejected demands per switch
        #     S[<switch>] = (accepted/rejected)
        self.S = dict()

        # Acceptance probability per class
        #     thresholds[0] = None
        #     thresholds[<class id>] = probability
        self.thresholds = list()
        self.thresholds.append(None)
        for i in range(1, self.NB_CLASSES + 1):
            if i < self.alpha:
                self.thresholds.append(1.0)
            else:
                self.thresholds.append(0.0)

        if not self.random:
            self.stochapp_thread = hub.spawn(self._continuous_STOCHAPP)


        # History of flow decisions
        self.flows = dict()
        # Monitoring
        self.sleep = 5
        self.datapaths = {}
        self.port_stats = {}
        self.port_speed = {}
        self.monitor_thread = hub.spawn(self._monitor)


        # == flow class predictor
        self.predictor = dict()    # predictor[<source port>] = <flow class>
        with open("flow.dat") as f:
            for line in f:
                line = line.strip()
                (sport, s_class, size) = line.split()
                self.predictor[int(sport)] = int(s_class)
        # ====================================================================
        # OVS1
        self.mac_to_port.setdefault(8796752236495, {})
        # local
        self.mac_to_port[8796752236495]["08:00:27:a5:30:72"] = 3 # gen1
        self.mac_to_port[8796752236495]["08:00:27:c2:f9:9a"] = 4 # hadoop1
        self.mac_to_port[8796752236495]["08:00:27:45:16:ee"] = 5 # hadoop2

        # remote
        self.mac_to_port[8796752236495]["08:00:27:69:cf:75"] = 2 # gen2
        self.mac_to_port[8796752236495]["08:00:27:f3:c7:2e"] = 2 # hadoop4
        self.mac_to_port[8796752236495]["08:00:27:04:5c:cd"] = 2 # hadoop5
	# OVS2
        self.mac_to_port.setdefault(8796750974788, {})
        # local
        self.mac_to_port[8796750974788]["08:00:27:69:cf:75"] = 3 # gen2
        self.mac_to_port[8796750974788]["08:00:27:f3:c7:2e"] = 4 # hadoop4
        self.mac_to_port[8796750974788]["08:00:27:04:5c:cd"] = 5 # hadoop5
        # remote
        self.mac_to_port[8796750974788]["08:00:27:a5:30:72"] = 2 # gen1
        self.mac_to_port[8796750974788]["08:00:27:c2:f9:9a"] = 2 # hadoop1
        self.mac_to_port[8796750974788]["08:00:27:45:16:ee"] = 2 # hadoop2
        # ==============================
        print time(), "c:", self.c, "seed:", self.seed, "epsilon:", self.epsilon, "#classes:", self.NB_CLASSES, "random:", self.random




    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, idle_timeout=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        if idle_timeout:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst, idle_timeout=idle_timeout,flags=ofproto.OFPFF_SEND_FLOW_REM)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    def _get_flow_info(self, pkt, in_port):
        """
        Get flow information from packet

	Returns the Flow corresponding to packet pkt. In case the protocol is
        not supported a None is returned.
        """
        flow = None

        # Ethernet frame
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        ethertype = eth_pkt.ethertype

        # IPv4?
        if ethertype == ether_types.ETH_TYPE_IP:
           ip_pkt = pkt.get_protocol(ipv4.ipv4)
           flow = Flow(src = ip_pkt.src, dst = ip_pkt.dst, proto = ip_pkt.proto, in_port = in_port, predictor=self.predictor)
 
           # TCP?
           if ip_pkt.proto == inet.IPPROTO_TCP:
              tcp_pkt = pkt.get_protocol(tcp.tcp)
              flow.sport = tcp_pkt.src_port
              flow.dport = tcp_pkt.dst_port

           # UDP?
           elif ip_pkt.proto == inet.IPPROTO_UDP:
              udp_pkt = pkt.get_protocol(udp.udp)
              flow.sport = udp_pkt.src_port
              flow.dport = udp_pkt.dst_port

           # ICMP?
           elif ip_pkt.proto == inet.IPPROTO_ICMP:
              pass

           # something else: not supported
           else:
              flow = None

        return flow

    def proba_size_class(self, i):
        """
        Returns probability of seeing flow of class i
        
        uses 'self.observations_classes'
        """
        return float(self.observations_classes[i])/float(self.observations_classes[0])

    def increment_observation_size_class(self, i):
        """
        Increment by one the number of observations of flows of class i

        uses 'self.observations_classes'
        """
        self.observations_classes[i] = self.observations_classes[i] + 1
        self.observations_classes[0] = self.observations_classes[0] + 1
   
    def update_statistics(self, flow):
        """
        Update the statistics database according
        """
        size_class = flow.size_class()
        self.increment_observation_size_class(size_class)     

    def accept(self, flow):
        """
	Define wether or not we should accept the flow for optimal routing
        """
        if self.random:
            return (random() < self.c)
        else:
            return (random() < self.thresholds[flow.size_class()])


    def _continuous_STOCHAPP(self):
        """
        Recomputation of the threshold when needed
        """
        while True:
            self.STOCHAPP()
            hub.sleep(self.T)

    def STOCHAPP(self):
       now = time()

       # no need to recompute
       if now < self.last_update + self.T:
          return

       # compute Y
       all_accepted = 0.0
       all_observed = 0.0
       # count accepted and rejected flows on all switches
       for s in self.S:
          # get accepted and rejected
          (a,r) = self.S[s]
         
          # count accepted flows 
          all_accepted = all_accepted + a
          # count observed flows
          all_observed = all_observed + (a + r)

          # reset the switch counters for next round
          self.S[s] = (0,0)

       # no observations, nothing to do!
       if all_observed == 0.0:
          return

       Y = all_accepted / all_observed

       # compute alpha
       _nb_classes = len(self.thresholds) - 1
       self.alpha = max(0.0, min(_nb_classes, (self.alpha + self.epsilon  * (self.c - Y))))

       # Determine the threshold class
       _threshold = int(self.alpha + 1.0)
       assert(_threshold < len(self.thresholds))

       # Always accept most important classes OK
       for i in range(1, _threshold):
           self.thresholds[i] = 1.0

       # Never accept least important classes OK
       for i in range(_threshold + 1, len(self.thresholds)):
           self.thresholds[i] = 0.0

       # Probabilistic accept threshold class
       self.thresholds[_threshold] = self.alpha - int(self.alpha)

       print time(), "c:",self.c, "epsilon", self.epsilon, "Y:", Y, "alpha:", self.alpha, "threshold:", (_threshold, self.thresholds[_threshold]) #, "P_i:", [self.proba_size_class(i) for i in range(1, len(self.thresholds))]#, "u(alpha):",self.thresholds[1:]

       # reset everything
       self.last_update = time()
# ========== monitoring ==
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """
            Record datapath's info
        """
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %d', datapath.id)
                self.datapaths[datapath.id] = datapath
                self.port_speed.setdefault(datapath.id, {})
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %d', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(self.sleep)
            print time(), "ports speed", self.port_speed



    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    def _get_speed(self, now, pre, period):
        if period:
            return (now - pre) / (period)
        else:
            return 0

    def _get_time(self, sec, nsec):
        return sec + nsec / (10 ** 9)

    def _get_period(self, n_sec, n_nsec, p_sec, p_nsec):
        return self._get_time(n_sec, n_nsec) - self._get_time(p_sec, p_nsec)

    def _save_stats(self, _dict, key, value, length):
        if key not in _dict:
            _dict[key] = []
        _dict[key].append(value)

        if len(_dict[key]) > length:
            _dict[key].pop(0)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        state_len = 3
        body = ev.msg.body
    
        for stat in sorted(body, key=attrgetter('port_no')):
            if stat.port_no != ofproto_v1_3.OFPP_LOCAL:
                key = (ev.msg.datapath.id, stat.port_no)
                value = (
                    stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
                    stat.duration_sec, stat.duration_nsec)
    
                self._save_stats(self.port_stats, key, value, state_len)
    
                # Get port speed.
                pre = 0
                period = self.sleep
                tmp = self.port_stats[key]
                if len(tmp) > 1:
                    pre = tmp[-2][0] + tmp[-2][1]
                    period = self._get_period(
                        tmp[-1][3], tmp[-1][4],
                        tmp[-2][3], tmp[-2][4])
    
                speed = self._get_speed(
                    self.port_stats[key][-1][0]+self.port_stats[key][-1][1],
                    pre, period)
    
#                self._save_stats(self.port_speed, key, speed, state_len)
#                print time(), "speed of ", key, ":",speed
                self.port_speed[ev.msg.datapath.id][stat.port_no] = speed 

# ========================


    # == Flow_removed
    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _flow_removed_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto

        if msg.reason == ofp.OFPRR_IDLE_TIMEOUT:
            reason = 'IDLE TIMEOUT'
        elif msg.reason == ofp.OFPRR_HARD_TIMEOUT:
            reason = 'HARD TIMEOUT'
        elif msg.reason == ofp.OFPRR_DELETE:
            reason = 'DELETE'
        elif msg.reason == ofp.OFPRR_GROUP_DELETE:
            reason = 'GROUP DELETE'
        else:
            reason = 'unknown'

        self.logger.info('OFPFlowRemoved received: '
                'cookie=%d priority=%d reason=%s table_id=%d '
                'duration_sec=%d duration_nsec=%d '
                'idle_timeout=%d hard_timeout=%d '
                'packet_count=%d byte_count=%d match.fields=%s',
                msg.cookie, msg.priority, reason, msg.table_id,
                msg.duration_sec, msg.duration_nsec,
                msg.idle_timeout, msg.hard_timeout,
                msg.packet_count, msg.byte_count, msg.match)

    # == Packet_in

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src

        # hadoop3 should never be seen!
        if dst == "08:00:27:31:ae:1e":
            assert(False)
            return

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']

###        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        if src not in self.mac_to_port[dpid]:
            self.mac_to_port[dpid][src] = in_port
            print time(), "MAC", src, "learned on ", dpid, " - " ,in_port
            assert(False)


        # == Output port =====================================================
        # if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            print time(), "Flooding not supported", dst
            out_port = ofproto.OFPP_FLOOD
            assert(False)


        # recompute thresholds
#        if not self.random:
#            self.STOCHAPP()

        # extract flow info
        flow = self._get_flow_info(pkt, in_port)

        optimize_flow = False
        # == Flow analysis to check for optimality ===================================================
        ########### ONLY for packets to the core ===========================
        if flow and (in_port != 1 and in_port != 2):
            print time(), "flow", flow ," from the edge on ", dpid 

            # ignore burst of packet_in for a flow
            if flow in self.flows:
               if self.flows[flow] >= (time() - 3.0):
                   print time(), "ignore burst of packet_in for one flow"
                   return
               self.flows[flow] = time()

            # Shall we optimize?
            # always optimize non best effort traffic
            optimize_flow = True    # Shall we optimize the flow?

            # determine if a best effort flow can be optimized
            if flow.is_best_effort():
               (a,r) = (0,0)
               if dpid in self.S:
                   (a,r) = self.S[dpid]

               # worth installing?
               if self.accept(flow):
                  optimize_flow = True
                  a = a + 1
               else:
                  optimize_flow = False
                  r = r + 1

               # keep track of statistics on flows and acceptances/rejections
               self.update_statistics(flow)
               self.S[dpid] = (a,r)

            ###### OUTPUT PORT
#DSA#            out_port = self.mac_to_port[dpid][dst]
            if out_port == 2:
                print time(), " ",dpid, "optimize flow ", flow, ": ", optimize_flow
                # force big best effort flows on 1
                if flow.is_best_effort() and optimize_flow:
                    out_port = 1
                    print time(), " ", dpid, "force ", flow, " on 1", out_port
                # load balance between 1 and 2 for other traffic
#DSA#                else:
#DSA#                    # load balance flows on link 1 and link 2
#DSA#                    # quick dirty hack
#DSA#    
#DSA#                    # get the current bw of the link
#DSA#                    speed1 = 0.0
#DSA#                    speed2 = 0.0
#DSA#                    if dpid in self.port_speed:
#DSA#                        if 1 in self.port_speed[dpid]:
#DSA#                            speed1 = float(self.port_speed[dpid][1])
#DSA#                        if 2 in self.port_speed[dpid]:
#DSA#                            speed2 = float(self.port_speed[dpid][2])
#DSA#    
#DSA#                    # load preferably the least used link
#DSA#                    if speed1 == 0.0 and speed2 == 0.0:
#DSA#                       fraction = 0.5
#DSA#                    else:
#DSA#                      fraction = 1.0 - (speed1 / (speed1 + speed2))
#DSA#                    fraction = max(0.1, min(fraction, 0.9))
#DSA#                    if random() < fraction:
#DSA#                        out_port = 1
#DSA#                    else:
#DSA#                        out_port = 2
#DSA#                    print time(), " ",dpid, "load balance ", flow, " on ", out_port, " (",fraction,")"           

        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            if flow:
                match = flow.match(parser)
                prio = 42
                if optimize_flow:
                    prio = 69
                self.add_flow(datapath, prio, match, actions, idle_timeout=180)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)

