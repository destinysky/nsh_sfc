#!/usr/bin/python
 
"""
"""
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch,UserSwitch
#OVSLegacyKernelSwitch, UserSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import Link, TCLink
 
#conf_port=50000
conf_ip_1='10.0.0.254'
conf_mac_1='11:12:13:14:15:16'

def topology():
    "Create a network."
    net = Mininet( controller=RemoteController, link=TCLink, switch=OVSKernelSwitch )
 
    print "*** Creating nodes"
    h1 = net.addHost( 'h1', mac='00:00:00:00:00:01', ip='10.0.0.1/24' )
    h2 = net.addHost( 'h2', mac='00:00:00:00:00:02', ip='10.0.0.2/24' )
    h3 = net.addHost( 'h3', mac='00:00:00:00:00:03', ip='10.0.0.3/24' )
    h4 = net.addHost( 'h4', mac='00:00:00:00:00:04', ip='10.0.0.4/24' )
    h5 = net.addHost( 'h5', mac='00:00:00:00:00:05', ip='10.0.0.5/24' )

    s1 = net.addSwitch( 's1', listenPort=6671 )
    s2 = net.addSwitch( 's2', listenPort=6672 )
    s3 = net.addSwitch( 's3', listenPort=6673 )
    s4 = net.addSwitch( 's4', listenPort=6674 )
    s5 = net.addSwitch( 's5', listenPort=6675 )

    c1 = net.addController( 'c1', controller=RemoteController, ip='127.0.0.1', port=6633 )

    print "*** Creating links"
    
    net.addLink(s1, h1)
    net.addLink(s2, h2)
    net.addLink(s3, h3)
    net.addLink(s4, h4)
    net.addLink(s5, h5)

    net.addLink(s1, s2)
    net.addLink(s2, s3)
    net.addLink(s3, s4)
    net.addLink(s4, s5)


    print "*** Starting network"
    net.build()

    h1.cmd('ip route add '+conf_ip_1+'/32 dev h1-eth0')
    h1.cmd('sudo arp -i h1-eth0 -s '+conf_ip_1+' '+conf_mac_1)
    h1.cmd('sysctl -w net.ipv4.ip_forward=1')
    h1.cmd('python3 listen.py &')

    h2.cmd('ip route add '+conf_ip_1+'/32 dev h2-eth0')
    h2.cmd('sudo arp -i h2-eth0 -s '+conf_ip_1+' '+conf_mac_1)
    h2.cmd('sysctl -w net.ipv4.ip_forward=1')
    h2.cmd('python3 listen.py &')

    h3.cmd('ip route add '+conf_ip_1+'/32 dev h3-eth0')
    h3.cmd('sudo arp -i h3-eth0 -s '+conf_ip_1+' '+conf_mac_1)
    h3.cmd('sysctl -w net.ipv4.ip_forward=1')
    h3.cmd('python3 listen.py &')

    h4.cmd('ip route add '+conf_ip_1+'/32 dev h4-eth0')
    h4.cmd('sudo arp -i h4-eth0 -s '+conf_ip_1+' '+conf_mac_1)
    h4.cmd('sysctl -w net.ipv4.ip_forward=1')
    h4.cmd('python3 listen.py &')

    h5.cmd('ip route add '+conf_ip_1+'/32 dev h5-eth0')
    h5.cmd('sudo arp -i h5-eth0 -s '+conf_ip_1+' '+conf_mac_1)
    h5.cmd('sysctl -w net.ipv4.ip_forward=1')
    h5.cmd('python3 listen.py &')

    c1.start()
    s1.start( [c1] )
    s2.start( [c1] )
    s3.start( [c1] )
    s4.start( [c1] )
    s5.start( [c1] )

    print "*** Running CLI"
    CLI( net )
 
    print "*** Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    topology()