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
from random import random
from time import time
# ====

class Flow:
    def __init__(self, src=None, dst=None, proto=None, in_port=None):
        self.src = src
        self.dst = dst
        self.proto = proto
        self.sport = None
        self.dport = None
        self.in_port = in_port
        self._size_class = None
        self.size_class()

    # == Size predictor
    def size_class(self):
        if self._size_class == None:
           self._size_class = 2 if random() > 1.0 else 1
        
        return self._size_class

    # == tuple matching
    def _matchTCP(self, parser):
        match = parser.OFPMatch(in_port=self.in_port, eth_type=0x0800, ipv4_src=self.src, ipv4_dst=self.dst, ip_proto=6, tcp_src=self.sport, tcp_dst=self.dport)
        return match

    def _matchUDP(self, parser):
        match = parser.OFPMatch(in_port=self.in_port, eth_type=0x0800, ipv4_src=self.src, ipv4_dst=self.dst, ip_proto=17, udp_src=self.sport, udp_dst=self.dport)
        return match

    def _matchICMP(self, parser):
####        print "Install ICMP!"
        match = parser.OFPMatch(in_port=self.in_port, eth_type=0x0800, ipv4_src=self.src, ipv4_dst=self.dst, ip_proto=1)
        return match

    def match(self, parser):
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
       
        # == flows ==================================
        self.G = nx.Graph()
        self.last_update = time()
        self.S = dict()
        self.thresholds = [None, 0.0, 0.0]
        self.observations_classes = [0, 0, 0]
        self.c = .7
        self.alpha = 1.0
        # ===========================================

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
        """
        # Ethernet frame
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        ethertype = eth_pkt.ethertype
        flow = None

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
        size_class = flow.size_class()

        self.increment_observation_size_class(size_class)     
###        print "Stats: ", [self.proba_size_class(i) for i in range(1,3)]

    def accept(self, flow):
        return (random() < self.thresholds[flow.size_class()])

    def STOCHAPP(self):
       now = time()

       # no need to recompute
       if now < self.last_update + 1.0:
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
       epsilon = 0.25

       self.alpha = max( 0.0, min(2.0, (self.alpha + epsilon  * (self.c - Y))))

       # Determine the threshold class
       _threshold = int(self.alpha + 1.0)
       assert(_threshold < len(self.thresholds))

#       _threshold = max(0, min(len(self.thresholds), int(self.alpha)))


       # Always accept most important classes OK
       for i in range(1, _threshold):
           self.thresholds[i] = 1.0

       # Never accept least important classes OK
       for i in range(_threshold + 1, len(self.thresholds)):
           self.thresholds[i] = 0.0

       # Probabilistic accept threshold class
       if _threshold < len(self.thresholds):
          self.thresholds[_threshold] = self.alpha - int(self.alpha)

       print "c:",self.c, "epsilon", epsilon, "Y:", Y, "alpha:", self.alpha, "P_i:", [self.proba_size_class(i) for i in range(1, len(self.thresholds))], "u(alpha):",self.thresholds[1:]

       # compute threshold
       

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

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']

###        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

###        print "MAC", src, "learned on ", in_port

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

        if flow:
           (a,r) = self.S.setdefault(vdpid, (0,0))
           # worth installing?

           if self.accept(flow):
####              print "Worth installing flow"
              a = a + 1
           else:
###              print "Not worth installing flow"
              r = r + 1

           # keep track of statistics for the flow
           self.update_statistics(flow)
           self.S[vdpid] = (a,r)

###           print "\t", flow

        # recompute thresholds
        self.STOCHAPP()

        # == Output port =====================================================

        # if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            if flow:
###                print "\tInstall IPv4 flow:", flow
                match = flow.match(parser)
                self.add_flow(datapath, 42, match, actions)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)
