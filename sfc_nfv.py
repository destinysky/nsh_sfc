import sqlite3
import json
import copy
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,CONFIG_DISPATCHER,DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import udp
from ryu.lib.packet import ipv4

from ext import nsh

db_name='nfv.sqlite'
conf_port=60000
conf_ip_1='10.0.0.254'
conf_mac_1='11:12:13:14:15:16'

class SFCController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(SFCController, self).__init__(req, link, data, **config)
        self.sfc_api_app = data['sfc_api_app']
    @route('add-flow', '/add_flow/{flow_id}', methods=['GET'])
    def api_add_flow(self,req, **kwargs):
        sfc_app = self.sfc_api_app
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute('''select * from flows where id = ?''',(kwargs['flow_id'],))
        flow_spec = cur.fetchone()
        if not flow_spec: return Response(status = 404)
        while flow_spec:
            (flow_id,name,eth_dst,eth_src,eth_type,ip_proto,ipv4_src,ipv4_dst,tcp_src,tcp_dst,udp_src,udp_dst,ipv6_src,ipv6_dst,service_id)=flow_spec
            if not eth_type:
                if ipv4_src or ipv4_dst: eth_type = 0x0800
                elif ipv6_src or ipv6_dst: eth_type = 0x86DD
            #elif not eth_type: eth_type = 0x0800
            if not ip_proto:
                if tcp_src or tcp_dst: ip_proto = 0x06 
                elif udp_src or udp_src: ip_proto = 0x11
            actions = []
            for dp in sfc_app.datapaths.values():
                match_add = sfc_app.create_match(dp.ofproto_parser, [
                                               (dp.ofproto.OXM_OF_ETH_SRC,eth_src),
                                               (dp.ofproto.OXM_OF_ETH_DST,eth_dst),
                                               (dp.ofproto.OXM_OF_ETH_TYPE,eth_type),
                                               (dp.ofproto.OXM_OF_IPV4_SRC,sfc_app.ipv4_to_int(ipv4_src)),
                                               (dp.ofproto.OXM_OF_IPV4_DST,sfc_app.ipv4_to_int(ipv4_dst)),
                                               (dp.ofproto.OXM_OF_IP_PROTO,ip_proto),
                                               (dp.ofproto.OXM_OF_TCP_SRC,tcp_src),
                                               (dp.ofproto.OXM_OF_TCP_DST,tcp_dst),
                                               (dp.ofproto.OXM_OF_UDP_SRC,udp_src),
                                               (dp.ofproto.OXM_OF_UDP_DST,udp_dst),
                                               (dp.ofproto.OXM_OF_IPV6_SRC,ipv6_src),
                                               (dp.ofproto.OXM_OF_IPV6_DST,ipv6_dst)
                                               ])
            
                sfc_app.add_flow(dp, 8, match_add, actions, metadata=flow_id, goto_id=2)
            
            flow_spec = cur.fetchone()
        conn.commit()
        cur.close()
        return Response(status = 200)

    @route('delete-flow', '/delete_flow/{flow_id}', methods=['GET'])
    def api_delete_flow(self,req, **kwargs):
        sfc_app = self.sfc_api_app
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute('''select * from flows where id = ?''',(kwargs['flow_id'],))
        flow_spec = cur.fetchone()
        conn.commit()
        cur.close()
        if not flow_spec: return Response(status = 404)
        (flow_id,name,eth_dst,eth_src,eth_type,ip_proto,ipv4_src,ipv4_dst,tcp_src,tcp_dst,udp_src,udp_dst,ipv6_src,ipv6_dst,service_id)=flow_spec
        if not eth_type:
                if ipv4_src or ipv4_dst: eth_type = 0x0800
                elif ipv6_src or ipv6_dst: eth_type = 0x86DD
            #elif not eth_type: eth_type = 0x0800
        if not ip_proto:
            if tcp_src or tcp_dst: ip_proto = 0x06 
            elif udp_src or udp_src: ip_proto = 0x11
        for dp in sfc_app.datapaths.values():
            # delete writemeta
            match_del = sfc_app.create_match(dp.ofproto_parser, [
                                               (dp.ofproto.OXM_OF_ETH_SRC,eth_src),
                                               (dp.ofproto.OXM_OF_ETH_DST,eth_dst),
                                               (dp.ofproto.OXM_OF_ETH_TYPE,eth_type),
                                               (dp.ofproto.OXM_OF_IPV4_SRC,sfc_app.ipv4_to_int(ipv4_src)),
                                               (dp.ofproto.OXM_OF_IPV4_DST,sfc_app.ipv4_to_int(ipv4_dst)),
                                               (dp.ofproto.OXM_OF_IP_PROTO,ip_proto),
                                               (dp.ofproto.OXM_OF_TCP_SRC,tcp_src),
                                               (dp.ofproto.OXM_OF_TCP_DST,tcp_dst),
                                               (dp.ofproto.OXM_OF_UDP_SRC,udp_src),
                                               (dp.ofproto.OXM_OF_UDP_DST,udp_dst),
                                               (dp.ofproto.OXM_OF_IPV6_SRC,ipv6_src),
                                               (dp.ofproto.OXM_OF_IPV6_DST,ipv6_dst)
                                               ])
            match = copy.copy(match_del)
            sfc_app.del_flow(datapath=dp,match=match)

            # delete spi match
            match = dp.ofproto_parser.OFPMatch(eth_type=0x894F, nsh_spi=int(service_id))
            sfc_app.del_flow(datapath=dp,match=match)
        return Response(status = 200)  

class sfc_app (app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = { 'wsgi': WSGIApplication}
    def __init__(self, *args, **kwargs):
        super(sfc_app, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(SFCController, {'sfc_api_app': self})
        self.datapaths = {}
    
######### Register/Unregister DataPathes in datapth dictionary
    @set_ev_cls(ofp_event.EventOFPStateChange,
            [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.info('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]
    
########## Setting default rules upon DP is connectted
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

################# Set flow to retrieve registration packet
        match = parser.OFPMatch(eth_type=0x0800, eth_dst=conf_mac_1, ipv4_dst=conf_ip_1, ip_proto = 17 , udp_dst=conf_port)
        actions = []
        self.add_flow(datapath, 10, match, actions,goto_id=2)
### decrease TTL of nsh

        #Bug in ovs: NXActionDecNshTtl doesnot work well on ovs, it discards all nsh packets, each effect try to modify ttl in nsh is failed. I guess this function didnot change the old cnum of ethernet
        match = parser.OFPMatch(eth_type=0x894F)
        #actions = [parser.NXActionDecNshTtl()]
        actions=[]
        self.add_flow(datapath, 9, match, actions,goto_id=1)

############### Default actions to tables 0, 1, 2
        ### Defination of Table0, default send all packets to table 3
        actions = []
        match = parser.OFPMatch()
        self.add_flow(datapath, 0, match, actions,goto_id=3)
        
        ### Defination of Table1, default send all nsh packets to table 3
        actions = []
        match = parser.OFPMatch()
        self.add_flow(datapath, 0, match, actions,table_id=1,goto_id=3)

        ### Defination of Table2, upload configure from json to controller 
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
           ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions,table_id=2)

        ### Defination of Table3, normal transform
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL,
           ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions,table_id=3)
    
################ Packet_IN handler ####################
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        actions = []
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto 
        parser = datapath.ofproto_parser 

        if msg.reason == ofproto.OFPR_NO_MATCH:
            reason = 'NO MATCH'
        elif msg.reason == ofproto.OFPR_ACTION:
            reason = 'ACTION'
        elif msg.reason == ofproto.OFPR_INVALID_TTL:
            reason = 'INVALID TTL'
        else:
            reason = 'unknown'
        self.logger.debug('OFPPacketIn received: '
                          'buffer_id=%x total_len=%d reason=%s '
                          'table_id=%d cookie=%d  match=%s ',
                           msg.buffer_id, msg.total_len, reason,
                           msg.table_id,  msg.cookie, msg.match )

######## register json nfv information
        
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)

        pkt_eth = pkt.get_protocol(ethernet.ethernet)
        eth_dst = pkt_eth.dst

        ipv4_header = None
        pkt_udp = None
        
        if pkt_eth and pkt_eth.ethertype == 0x0800:
            ipv4_header = pkt.get_protocol(ipv4.ipv4)
            dst_ip = ipv4_header.dst
        if ipv4_header and ipv4_header.proto == 0x11:
            pkt_udp = pkt.get_protocol(udp.udp)

        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        
        if msg.table_id== 2:
            if pkt_udp and (dst_ip == conf_ip_1) and (eth_dst == conf_mac_1) :
                if pkt_udp.dst_port == conf_port:
                    self.logger.info ("Configure packet has arrived")
                    reg_string=pkt.protocols[-1]
                    reg_info = json.loads(reg_string)
                    name=reg_info['name']
                    id=reg_info['vnf_id']
                    type_id=reg_info['type_id']
                    group_id=reg_info['group_id']
                    geo_location=reg_info['geo_location']
                    iftype=reg_info['iftype']
                    bidirectional=reg_info['bidirectional']
                    dpid=datapath.id
                    locator_addr=pkt_eth.src

                    cur.execute('''INSERT OR IGNORE INTO vnf (id, name, type_id,
                            group_id, geo_location, iftype, bidirectional,
                            dpid, in_port, locator_addr  ) VALUES ( ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ? )''', ( id, name, type_id,
                                group_id, geo_location, iftype,
                                bidirectional, dpid, in_port, locator_addr )
                            )
        
        try:
            flow_match = msg.match['metadata']
            in_port_entry = msg.match['in_port']
            dp_entry_point = datapath
            if msg.table_id == 2:
                cur.execute('''select * from flows where id = ? ''',(flow_match,))
                flow_spec = cur.fetchone()
                (flow_id,name,eth_dst,eth_src,eth_type,ip_proto,ipv4_src,ipv4_dst,tcp_src,tcp_dst,udp_src,udp_dst,ipv6_src,ipv6_dst,service_id)=flow_spec
                if not eth_type:
                    if ipv4_src or ipv4_dst: eth_type = 0x0800
                    elif ipv6_src or ipv6_dst: eth_type = 0x86DD
                #elif not eth_type: eth_type = 0x0800
                if not ip_proto:
                    if tcp_src or tcp_dst: ip_proto = 0x06 
                    elif udp_src or udp_src: ip_proto = 0x11 
                actions_entry_point = []  
                match_entry_point = self.create_match(parser, [
                                                (ofproto.OXM_OF_IN_PORT,in_port_entry),
                                                (ofproto.OXM_OF_ETH_SRC,eth_src),
                                                (ofproto.OXM_OF_ETH_DST,eth_dst),
                                                (ofproto.OXM_OF_ETH_TYPE,eth_type),
                                                (ofproto.OXM_OF_IPV4_SRC,self.ipv4_to_int(ipv4_src)),
                                                (ofproto.OXM_OF_IPV4_DST,self.ipv4_to_int(ipv4_dst)),
                                                (ofproto.OXM_OF_IP_PROTO,ip_proto),
                                                (ofproto.OXM_OF_TCP_SRC,tcp_src),
                                                (ofproto.OXM_OF_TCP_DST,tcp_dst),
                                                (ofproto.OXM_OF_UDP_SRC,udp_src),
                                                (ofproto.OXM_OF_UDP_DST,udp_dst),
                                                (ofproto.OXM_OF_IPV6_SRC,ipv6_src),
                                                (ofproto.OXM_OF_IPV6_DST,ipv6_dst)
                                                ])
                
                #### DELETE PREINSTALLED CATCHING FLOWS
                match_common = self.create_match(parser, [
                                                (ofproto.OXM_OF_ETH_SRC,eth_src),
                                                (ofproto.OXM_OF_ETH_DST,eth_dst),
                                                (ofproto.OXM_OF_ETH_TYPE,eth_type),
                                                (ofproto.OXM_OF_IPV4_SRC,self.ipv4_to_int(ipv4_src)),
                                                (ofproto.OXM_OF_IPV4_DST,self.ipv4_to_int(ipv4_dst)),
                                                (ofproto.OXM_OF_IP_PROTO,ip_proto),
                                                (ofproto.OXM_OF_TCP_SRC,tcp_src),
                                                (ofproto.OXM_OF_TCP_DST,tcp_dst),
                                                (ofproto.OXM_OF_UDP_SRC,udp_src),
                                                (ofproto.OXM_OF_UDP_DST,udp_dst),
                                                (ofproto.OXM_OF_IPV6_SRC,ipv6_src),
                                                (ofproto.OXM_OF_IPV6_DST,ipv6_dst)
                                                ])
                for dp in self.datapaths.values():
                    match = copy.copy(match_common)
                    self.del_flow(datapath=dp,match=match)

                # look up the length of spi
                cur.execute('''select vnf_id from service where service_id = ?''',(service_id,))
                len_spi = int(len(cur.fetchall()))
                last_si=len_spi
                # look up the first VNF
                cur.execute('''select vnf_id from service where service_id = ? and  prev_vnf_id is NULL  ''',(service_id,))
                vnf_id = cur.fetchone()[0]
                cur.execute(''' select bidirectional from vnf where id=?''',(vnf_id,))
                bidirectional=cur.fetchone()[0]
                if bidirectional=='True':
                    cur.execute(''' select locator_addr, dpid, in_port from vnf where id=? and iftype == 3''',(vnf_id,))
                    locator_addr,dpid, in_port = cur.fetchone()
                actions_entry_point += [parser.NXActionEncapNsh()]
                actions_entry_point += [parser.OFPActionSetField(nsh_spi=int(service_id))]
                actions_entry_point += [parser.OFPActionSetField(nsh_si=int(len_spi))]
                actions_entry_point += [parser.NXActionEncapEther()]
                actions_entry_point += [parser.OFPActionSetField(eth_dst=locator_addr)]
                actions_entry_point += [parser.OFPActionSetField(eth_src=pkt_eth.src)]
                self.add_flow(dp_entry_point, 8, match_entry_point, actions_entry_point,goto_id=3)
                last_loc=locator_addr

                while True:
                    datapath = self.datapaths[dpid]
                    actions = []
                    match = None
                    cur.execute('''select next_vnf_id from service where service_id = ? and vnf_id = ?  ''',(service_id,vnf_id))
                    next_vnf_id = cur.fetchone()[0]
                    if next_vnf_id:
                        cur.execute(''' select bidirectional from vnf where id=?''',(next_vnf_id,))
                        bidirectional=cur.fetchone()[0]
                        if bidirectional=='True':
                            cur.execute(''' select locator_addr, dpid, in_port from vnf where id=? and iftype == 3''',(next_vnf_id,))
                            locator_addr,dpid, in_port2 = cur.fetchone()
                            cur.execute('''select service_index from service where service_id = ? and vnf_id = ?  ''',(service_id,next_vnf_id))
                            current_si = cur.fetchone()[0]

                            ### for proxy
                            match = parser.OFPMatch(eth_type=0x894F,nsh_spi=int(service_id),nsh_si=int(current_si))
                            actions.append(parser.OFPActionSetField(eth_dst=locator_addr))
                            self.add_flow(datapath, 8, match,  actions, metadata=flow_id, table_id=1, goto_id=3)

                            ### for no-proxy
                            cur.execute('''select * from flows where id = ? ''',(flow_match,))
                            flow_spec = cur.fetchone()
                            (flow_id,name,eth_dst,eth_src,eth_type,ip_proto,ipv4_src,ipv4_dst,tcp_src,tcp_dst,udp_src,udp_dst,ipv6_src,ipv6_dst,service_id)=flow_spec
                            if not eth_type:
                                if ipv4_src or ipv4_dst: eth_type = 0x0800
                                elif ipv6_src or ipv6_dst: eth_type = 0x86DD
                            #elif not eth_type: eth_type = 0x0800
                            if not ip_proto:
                                if tcp_src or tcp_dst: ip_proto = 0x06 
                                elif udp_src or udp_src: ip_proto = 0x11 
                            match = self.create_match(parser, [
                                            (ofproto.OXM_OF_IN_PORT,in_port),
                                            (ofproto.OXM_OF_ETH_TYPE,eth_type),
                                            (ofproto.OXM_OF_IPV4_SRC,self.ipv4_to_int(ipv4_src)),
                                            (ofproto.OXM_OF_IPV4_DST,self.ipv4_to_int(ipv4_dst)),
                                            (ofproto.OXM_OF_IP_PROTO,ip_proto),
                                            (ofproto.OXM_OF_TCP_SRC,tcp_src),
                                            (ofproto.OXM_OF_TCP_DST,tcp_dst),
                                            (ofproto.OXM_OF_UDP_SRC,udp_src),
                                            (ofproto.OXM_OF_UDP_DST,udp_dst),
                                            (ofproto.OXM_OF_IPV6_SRC,ipv6_src),
                                            (ofproto.OXM_OF_IPV6_DST,ipv6_dst)
                                            ])
                            actions=[]
                            actions += [parser.NXActionEncapNsh()]
                            actions += [parser.OFPActionSetField(nsh_spi=int(service_id))]
                            actions += [parser.OFPActionSetField(nsh_si=int(current_si))]
                            actions += [parser.NXActionEncapEther()]
                            actions += [parser.OFPActionSetField(eth_dst=locator_addr)]
                            actions += [parser.OFPActionSetField(eth_src=pkt_eth.src)]

                            self.add_flow(datapath, 6, match, actions,metadata=flow_id, table_id=0, goto_id=3)
                            
                            match = parser.OFPMatch(eth_type=0x894F,eth_dst=last_loc, nsh_spi=int(service_id),nsh_si=int(last_si))
                            actions = [parser.NXActionDecap(),parser.NXActionDecap(),parser.OFPActionOutput(int(in_port2))] 
                            self.add_flow(datapath, 6, match, actions,metadata=flow_id, table_id=1)
                            #match=None
                            #actions = [parser.OFPActionSetField(eth_dst=last_loc),parser.OFPActionOutput(int(in_port2))]
                            #self.add_flow(datapath, 6, match, actions, table_id=4)


                            last_si=current_si
                            last_loc=locator_addr
                            in_port=in_port2

                        vnf_id = next_vnf_id
                    else:
                        ### for proxy
                        actions = [parser.NXActionDecap(),parser.NXActionDecap()] 
                        match = parser.OFPMatch(eth_type=0x894F,nsh_spi=int(service_id),nsh_si=0)
                        self.add_flow(datapath, 8, match, actions,metadata=flow_id, table_id=1, goto_id=3)

                        ### for no-proxy, go to table 3
                        match = parser.OFPMatch(eth_type=0x894F,eth_dst=last_loc, nsh_spi=int(service_id),nsh_si=1)
                        actions = [parser.NXActionDecap(),parser.NXActionDecap(),parser.OFPActionOutput(int(in_port))] 
                        self.add_flow(datapath, 6, match, actions,metadata=flow_id, table_id=1)


                        break
                        



            # elif msg.table_id== 4:
            #     nsh_header=nsh.nsh.parser(msg.data)
            #     nsh_spi_r = nsh_header[0].spi
            #     nsh_si_r = nsh_header[0].si
            #     self.logger.info('NSH receive, nsh_spi = %d, nsh_si = %d', nsh_spi_r,nsh_si_r)
            #     match=parser.OFPMatch(priority=10, eth_type=0x894F,nsh_spi=int(service_id))
            #     self.del_flow(datapath=dp_entry_point,match=match,table_id=0)
            #     #delete

            #     while True:
            #         cur.execute('''select vnf_id,service_index from service where service_id = ?''',(nsh_spi_r,))
            #         vnf_id, service_index = cur.fetchone()
            #         cur.execute(''' select bidirectional from vnf where id=?''',(vnf_id,))
            #         bidirectional=cur.fetchone()[0]
            #         if bidirectional=='True':
            #             cur.execute(''' select locator_addr, dpid, in_port from vnf where id=? and iftype == 3''',(vnf_id,))
            #             locator_addr,dpid, in_port = cur.fetchone()
            #         actions=[]
            #         match = parser.OFPMatch(eth_type=0x894F,nsh_spi=int(nsh_spi_r),nsh_si=int(nsh_spi_r))
            #         #add



        except KeyError:
            flow_match = None
            pass
            

            
        conn.commit()
        cur.close()



############# Function definitions #############


    def add_flow(self, datapath, priority, match, actions,
            buffer_id=None, table_id=0,metadata=None,goto_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        

        if goto_id:
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

            if metadata:
                inst.append(parser.OFPInstructionWriteMetadata(metadata,0xffffffff))
            inst.append(parser.OFPInstructionGotoTable(goto_id))
        else:
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst,table_id=table_id)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst,
                                    table_id=table_id)
        datapath.send_msg(mod)

#############################################

    def del_flow(self, datapath, match,table_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if table_id:
            mod = parser.OFPFlowMod(datapath=datapath,
                        command=ofproto.OFPFC_DELETE,
                        out_port=ofproto.OFPP_ANY,
                        out_group=ofproto.OFPG_ANY,
                        match=match,table_id=table_id)
        else:
            mod = parser.OFPFlowMod(datapath=datapath,
                        command=ofproto.OFPFC_DELETE,
                        out_port=ofproto.OFPP_ANY,
                        out_group=ofproto.OFPG_ANY,
                        match=match)
        datapath.send_msg(mod)

############################################
    def create_match(self, parser, fields):
        """Create OFP match struct from the list of fields."""
        match = parser.OFPMatch()
        for a in fields:
            if  a[1]:
                match.append_field(*a)
        return match

###########################################
    def ipv4_to_int(self, string):
        ip = string.split('.')
        assert len(ip) == 4
        i = 0
        for b in ip:
            b = int(b)
            i = (i << 8) | b
        return i