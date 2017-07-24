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

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import in_proto as inet
from ryu.lib.packet import tcp
from ryu.lib.packet import udp

# ====
import networkx as nx
from random import seed
from random import random
from time import time
import os

class Flow:
    def __init__(self, src=None, dst=None, proto=None, in_port=None):
        self.src = src
        self.dst = dst
        self.proto = proto
        self.sport = None
        self.dport = None
        self.in_port = in_port

    # == Size predictor
    def size_class(self):
        assert(self.is_best_effort())
        return (self.dport - 10010)

    def is_best_effort(self):
        return (self.proto == 6 and (self.dport >= 10011 and self.dport <= 10013))

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
        # Topology graph
        self.G = nx.Graph()

        # Last time the threshold has been recomputed
        self.last_update = 0.0

        # Interval between two threshold recomputations (in seconds, float)
        self.T = 1.0

        # Number of flow classes
        self.NB_CLASSES = 3
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
            self.thresholds.append(0.0)

        # Average load on the controller (c \in \left[0; 1\right])
        self.c = 0.5
        if "ryu_c" in os.environ:
           self.c = float( os.environ["ryu_c"])
        self.random=False
        if "ryu_random" in os.environ:
           self.random = bool( int(os.environ["ryu_random"]))
        self.seed = 0
        if "ryu_XP" in os.environ:
           self.seed = int(os.environ["ryu_XP"])
        seed(int(self.seed))

        # Current alpha value
        self.alpha = 1.0

        # STOCHAPP Convergence parameter (epsilon \in \left[0; 1\right])
        self.epsilon = 0.25

        # History of flow decisions
        self.flows = dict()
        # ====================================================================
        # OVS1
        self.mac_to_port.setdefault(8796752236495, {})
        self.mac_to_port[8796752236495]["08:00:27:69:cf:75"] = 2 # gen2
        self.mac_to_port[8796752236495]["08:00:27:f3:c7:2e"] = 2 # hadoop4
        self.mac_to_port[8796752236495]["08:00:27:04:5c:cd"] = 2 # hadoop5
	# OVS2
        self.mac_to_port.setdefault(8796750974788, {})
        self.mac_to_port[8796750974788]["08:00:27:a5:30:72"] = 2 # gen1
        self.mac_to_port[8796750974788]["08:00:27:c2:f9:9a"] = 2 # hadoop1
        self.mac_to_port[8796750974788]["08:00:27:45:16:ee"] = 2 # Hadoop2
        # ==============================
        print "c:", self.c, "seed:", self.seed, "epsilon:", self.epsilon, "#classes:", self.NB_CLASSES, "random:", self.random

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

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
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
           flow = Flow(src = ip_pkt.src, dst = ip_pkt.dst, proto = ip_pkt.proto, in_port = in_port)
 
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

    def STOCHAPP(self):
       """
       Recomputation of the threshold when needed
       """
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

       print "c:",self.c, "epsilon", self.epsilon, "Y:", Y, "alpha:", self.alpha, "P_i:", [self.proba_size_class(i) for i in range(1, len(self.thresholds))], "u(alpha):",self.thresholds[1:]

       # reset everything
##############       self.observations_classes = [0, 0, 0]
       self.last_update = time()

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

        # dirty hack
        if dst == "08:00:27:31:ae:1e":
            return

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']

###        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        if src not in self.mac_to_port[dpid]:
            self.mac_to_port[dpid][src] = in_port
            print "MAC", src, "learned on ", dpid, " - " ,in_port

        # == Topology discovery ==============================================
        # add the switch
        if dpid not in self.G.nodes():
            self.G.add_node(dpid)

        # add the port
        vdpid = "%d:%d" % (dpid, in_port)
        if vdpid not in self.G.nodes():
            # add the port to the topology
            self.G.add_node(vdpid)
            # connect the port to its switch
            self.G.add_edge(vdpid, dpid)
       
        # add the host (i.e., MAC)
        if src not in self.G.nodes():
            self.G.add_node(src)

        # connect host to the port
        self.G.add_edge(src, vdpid)

        # == Flow analysis ===================================================
        # extract flow info
        flow = self._get_flow_info(pkt, in_port)

        optimize_flow = True    # Shall we optimize the flow?

        # determine if a best effort flow can be optimized
        if flow and flow.is_best_effort():
           (a,r) = self.S.setdefault(vdpid, (0,0))

           # worth installing?
           if self.accept(flow):
              optimize_flow = True
              a = a + 1
           else:
              optimize_flow = False
              r = r + 1

           # keep track of statistics for the flow
           self.update_statistics(flow)
           self.S[vdpid] = (a,r)

           # recompute thresholds
           self.STOCHAPP()

        # == Output port =====================================================

        # if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
            if out_port == 2 and flow and flow.is_best_effort() and optimize_flow:
               out_port = 1
        else:
            print "PAS ICI", dst
            out_port = ofproto.OFPP_FLOOD

        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            if flow:
                match = flow.match(parser)
                self.add_flow(datapath, 42, match, actions)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
#        if flow:
#            if flow in self.flows:
#                return
#            else:
#                self.flows[flow] = out_port
        datapath.send_msg(out)

