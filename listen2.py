import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor
import os
import json
import sys
#message:$$name,VNFid,type_id,group_id,iftype$$
#name=forwarder1, vnf_id=555, type_id=1, group_id=1, iftype=2, bidirectional=False, 

portLis=50001
ogeo_location='server1.rack2.row3.room4'
conf_ip='10.0.0.254'
conf_port=60000

class BgRec:
    def __init__(self, host, port):
        
        super(BgRec, self).__init__()
        
        self.pool = ThreadPoolExecutor(128)
        
        self.s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        
        self.buffer = ''
        
        self.s.bind((host,port))
    
    def close(self):
        global connected
        self.s.close()
        connected=False
        return
    
    def handle_read(self):
        #此处有拥塞可能
        self.pool.submit(self.recv)
            
    def recv(self):
        print('Listening...')
        while True:
            try:
                data,addr=self.s.recvfrom(2048)
            except:
                break
            if not data:
                break
            recvdata=''
            recvdata=str(data,'utf8')
            print(addr)
            print(recvdata)            
            #command=recvdata.split('$$')[1]
            #self.dealWithMsg(command,addr)
        
        
                
    def valid_ip(self,address):
        try: 
            ipaddress.ip_address(address)
            return True
        except:
            return False

#message:$$name,VNFid,type_id,group_id,iftype$$
    def dealWithMsg(self,command,addr):  
        oname=command.split(',')[0]
        oVNFid=command.split(',')[1]
        otype_id=command.split(',')[2]
        ogroup_id=command.split(',')[3]
        oiftype=command.split(',')[4]
        if(int(oiftype)==1 or int(oiftype)==2):
            obidirectional='False'
        elif(int(oiftype)==3):
            obidirectional='True'
            
        register_dict = dict(
            vnf_id = oVNFid,
            name=oname,
            type_id=otype_id,
            group_id=ogroup_id,
            geo_location=ogeo_location,
            iftype=oiftype,
            bidirectional=obidirectional)
        json_message = json.dumps(register_dict)

        try:
            s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error:
            print ('Failed to create socket')
            sys.exit()
        s2.sendto(json_message.encode(encoding='utf_8'), (conf_ip, conf_port ))


if __name__ == '__main__':
    bgrunner = BgRec('', portLis)
    bgrunner.recv()