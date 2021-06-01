# Network Service Header Based Service Function Chain Application
This is an application for Ryu controller. It implements NSH (RFC8300) with SFC (RFC7665).

## Background: Service Function Chain (SFC)

![background figure 1](https://github.com/destinysky/resources/raw/master/nsh_sfc/background1.png)

- A process can be divided into several functions. These functions form a service function chain in order.
   - Security function chain
      - Gateway, deep packet inspection, firewall, antivirus.
   - Video stream function chain
      - Mixer, compressor, transcoder.

It may change the path of packets. 

![background figure 2](https://github.com/destinysky/resources/raw/master/nsh_sfc/background2.png)

## Related Software
- [Ryu](https://osrg.github.io/ryu/) 
   > Ryu is a component-based software defined networking framework. 
   > Ryu provides software components with well defined API that make it easy for developers to create new network management and control applications.
- [Mininet](http://mininet.org/)
   > Mininet creates a realistic virtual network, running real kernel, switch and application code, on a single machine (VM, cloud or native), in seconds, with a single command
- [SQLite](https://www.sqlite.org/index.html)
   > SQLite is a C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine. 

## Objective
- Create a platform for the implement of SFC components: Classifier, Service Function Forwarder, SFC Proxy.
- Cooperate with VNF allocation model —— calculated by ILP approach or heuristic algorithm
- Implement with Network Service Header (NSH), a proposed protocol in RFC 8300 

## Structure
![structure](https://github.com/destinysky/resources/raw/master/nsh_sfc/structure.png)

1. User register the needed SFC to database
2. Allocation model calculates the allocation and sends the result to deployed nodes. 
3. The nodes install corresponding VNF and register the allocations to controller.
4. The controller store the allocations to database.
5. User register the source, destination and the chain id of a service through REST api.
6. Modify the flow table in switches according to the database

## Modules in application
![Modules](https://github.com/destinysky/resources/raw/master/nsh_sfc/modules%20in%20application.png)

1. WSGI: receives the request from REST api —— add or delete a service
2. VNF register: receives the self register information from nodes and stores them in database.
3. Detection entry: When a new flow is added, only one entry in flow table is added in each switch for detection. If the packet is detected, this entry on all switched are deleted and changed to the other entries. This entry reduces the size of flow table.
4. Source entry: located in the entrance of service flow, encapsulates the Type 1 NSH header, encapsulates Transport Encapsulation, decides the physical address of the next hop.
 5. Middle entry: located in the switches which are connected with SFs.
   - **For SFC-aware function**: routes the packet from the last hop to the connected SF, decides the physical address of the next hop of the packet from the connected SF.
   - **Otherwise**: decapsulates NSH header and Transport Encapsulation of the packet from the last hop , routes the decapsulated packet to the connected SF, encapsulates the Type 1 NSH header and Transport Encapsulation, decides the physical address of the next hop.
6. Destination entry: located in the switches which are connected with the last SFs of SFCs. 
   - **For SFC-aware function**: routes the packet from the last hop to the connected SF, routes the packet from the connected SF to the destination node.
   - **Otherwise**: decapsulates NSH header and Transport Encapsulation of the packet from the last hop , routes the decapsulated packet to the connected SF, routes the packet from the connected SF to the destination node.

## Flow tables
### Table 0:
<table>
   <tr>
      <td>Priority</td>
      <td>Match</td>
      <td>Action</td>
      <td>Note</td>
   </tr>
   <tr>
      <td>8</td>
      <td>conditions of the added flow</td>
      <td>write meta = flow id, go to table 2</td>
      <td>detection entry</td>
   </tr>
   <tr>
      <td>10</td>
      <td>mac address, ip address, port of register packet</td>
      <td>go to table 2</td>
      <td>VNF registry</td>
   </tr>
   <tr>
      <td>9</td>
      <td>NSH header</td>
      <td>Decrease NSH TTL, go to table 1</td>
      <td></td>
   </tr>
   <tr>
      <td>0</td>
      <td>-</td>
      <td>go to table 3</td>
      <td>default entry</td>
   </tr>
   <tr>
      <td>8</td>
      <td>conditions of the added flow</td>
      <td>encapsulate the Type 1 NSH header, set spi as service id, set si as the length of the SFC , encapsulate enthernet header, set the destination address as the address of the first SF of this SFC, set the source address as the address of the original one, go to table 3</td>
      <td>Source entry</td>
   </tr>
   <tr>
      <td>6</td>
      <td>conditions of the added flow</td>
      <td>encapsulate the Type 1 NSH header, set spi as service id, set si as the remaining length of the SFC, encapsulate enthernet header, set the destination address as the address of the next SF, set the source address as the address of this SF, go to table 3</td>
      <td>Middle entry For SFC-non-aware function,  packet to the next hop</td>
   </tr>
   <tr>
      <td></td>
   </tr>
</table>

### Table 1:
<table>
   <tr>
      <td>Priority</td>
      <td>Match</td>
      <td>Action</td>
      <td>Note</td>
   </tr>
   <tr>
      <td>8</td>
      <td>NSH header, spi, si</td>
      <td>Change the destination address to the address of the next hop, go to table 3</td>
      <td>Middle entry For SFC-aware function</td>
   </tr>
   <tr>
      <td>8</td>
      <td>NSH header, spi, si=0</td>
      <td>Decapsulate the NSH header and Ethernet header</td>
      <td>Destination entry For SFC-aware function</td>
   </tr>
   <tr>
      <td>6</td>
      <td>NSH header, spi, si</td>
      <td>Decapsulate the NSH header and enthernet header and output to the SF</td>
      <td>Middle entry For SFC-non-aware function, packet from the last hop</td>
   </tr>
   <tr>
      <td>6</td>
      <td>NSH header, spi, si=1, destination mac address = the address of the last SF</td>
      <td>Decapsulate the NSH header and Ethernet header and output to the last SF</td>
      <td>Destination entry For SFC-non-aware function</td>
   </tr>
   <tr>
      <td>0</td>
      <td>-</td>
      <td>Go to table 3</td>
      <td>Default entry</td>
   </tr>
</table>

### Table 2:
<table>
   <tr>
      <td>Priority</td>
      <td>Match</td>
      <td>Action</td>
      <td>Note</td>
   </tr>
   <tr>
      <td>0</td>
      <td>-</td>
      <td>Go to controller</td>
      <td>Default entry</td>
   </tr>
   <tr>
      <td></td>
   </tr>
</table>

### Table 3:
<table>
   <tr>
      <td>Priority</td>
      <td>Match</td>
      <td>Action</td>
      <td>Note</td>
   </tr>
   <tr>
      <td>0</td>
      <td>-</td>
      <td>Normal forwarding </td>
      <td>Default entry</td>
   </tr>
   <tr>
      <td></td>
   </tr>
</table>

## Interaction between controller and nodes
![Interaction](https://github.com/destinysky/resources/raw/master/nsh_sfc/Interaction%20between%20controller%20and%20nodes.png)

## Database
> Based on the database structure in [Service Function Chaining Application for Ryu SDN controller](https://github.com/abulanov/sfc_app)

![database1](https://github.com/destinysky/resources/raw/master/nsh_sfc/database1.png)
![database2](https://github.com/destinysky/resources/raw/master/nsh_sfc/database2.png)
![database3](https://github.com/destinysky/resources/raw/master/nsh_sfc/database3.png)

## Cooperation with VNF allocation model (Optional)
The allocation of VNFs can be input manually. It can also be allocated automatically by using VNF allocation model (Linear Programming approach or other algorithms).

![cooperation](https://github.com/destinysky/resources/raw/master/nsh_sfc/cooperation.png)


## Demonstration
### Brief:
#### Topology:
![Topology](https://github.com/destinysky/resources/raw/master/nsh_sfc/demo.png)
raw
#### Service: 1 → 2, 3 → 4 → 5
#### Objective function: minimize the maximum number of VNFs allocated to each nodes
![Objective](http://latex.codecogs.com/gif.latex?\\min\\max_{n\in%20N}\\sum_{r\\in%20R}{\\sum_{k\\in%20K_r}{x_{n}^{rk}}})

*N* is the set of nodes. *R* is the set of SFCs. ![](http://latex.codecogs.com/gif.latex?K_r) is the set of VNFs in SFC *r*. ![](http://latex.codecogs.com/gif.latex?x_n^{rk}=1)  VNF *k* in SFC *r* is allocated to node *n*, 0 otherwise.

### Software:
In this demo, Ryu 4.32, Mininet 2.3.0d6, Open vSwitch 2.12.0, Python 3.6.9, and Sqlite 2.8.17 are used.
[SQLite Browser](http://sqlitebrowser.org/) is optional but helpful.

### Steps:
1. Replace *ryu/ofproto/nicira_ext.py* and *ryu/ofproto/nx_actions.py* with [pull request #81 in Ryu](https://github.com/osrg/ryu/pull/81). You can also copy these two files in *ext* folder.
2. Run *ryu-manager sfc_nfv*, *sudo ./topology.py*
3. *pingall* in mininet
4. *xterm h1* in mininet (optional)
5. Run *test_sfc.py* by Python 3 (optional)
6. *h4 tracepath h5* and *h5 tracepath h4* in mininet, see the results
7. Run *curl -v 127.0.0.1:8080/add_flow/1* in a terminal.
8. *h4 tracepath h5* and *h5 tracepath h4* in mininet, see the results
9. Run *curl -v 127.0.0.1:8080/delete_flow/1* in a terminal.
10. *h4 tracepath h5* and *h5 tracepath h4* in mininet, see the results

### Result:
#### Imgs:
![](https://github.com/destinysky/resources/raw/master/nsh_sfc/regres.png)

![](https://github.com/destinysky/resources/raw/master/nsh_sfc/encap.png)

![](https://github.com/destinysky/resources/raw/master/nsh_sfc/before.png)

![](https://github.com/destinysky/resources/raw/master/nsh_sfc/after.png)


#### Video:
![demo_gif](https://github.com/destinysky/resources/raw/master/nsh_sfc/screencast.gif)
[![demo video](https://github.com/destinysky/resources/raw/master/nsh_sfc/Screencast_x264.mp4)]

## Files:
- sfc_nfv.py: Ryu application
- test_sfc.py: Allocation model.
- topology.py: Mininet topology.

## Citation:
If these codes are helpful to your work, please cite this paper. Thank you.
>R. Kang, F. He, T. Sato, and E. Oki, "Demonstration of Network Service Header Based Service Function Chain Application with Function Allocation Model," NOMS 2020 - 2020 IEEE/IFIP Network Operations and Management Symposium, Budapest, 2020, pp. 1-2.

>@INPROCEEDINGS{203830, 
author={R. {kang} and F. {He} and T. {Sato} and E. {Oki}}, 
booktitle={NOMS 2020 - 2020 IEEE/IFIP Network Operations and Management Symposium}, 
title={Demonstration of Network Service Header Based Service Function Chain Application with Function Allocation Model}, 
year={2020},
pages={1-2},
month={April},}


