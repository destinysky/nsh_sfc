# Network Service Header Based Service Function Chain Application
This is an application for Ryu controller. It implements NSH (RFC8300) with SFC (RFC7665).

## Background: Service Function Chain (SFC)

![background figure 1](https://github.com/destinysky/resources/blob/master/nsh_sfc/background1.png)

- A process can be divided into several functions. These functions form a service function chain in order.
   - Security function chain
      - Gateway, deep packet inspection, firewall, antivirus.
   - Video stream function chain
      - Mixer, compressor, transcoder.

It may change the path of packets. 

![background figure 2](https://github.com/destinysky/resources/blob/master/nsh_sfc/background2.png)

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
![structure](https://github.com/destinysky/resources/blob/master/nsh_sfc/structure.png)

1. User register the needed SFC to database
2. Allocation model calculates the allocation and sends the result to deployed nodes. 
3. The nodes install corresponding VNF and register the allocations to controller.
4. The controller store the allocations to database.
5. User register the source, destination and the chain id of a service through REST api.
6. Modify the flow table in switches according to the database

## Modules in application
![Modules](https://github.com/destinysky/resources/blob/master/nsh_sfc/modules%20in%20application.png)

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


## Interaction between controller and nodes
![Interaction](https://github.com/destinysky/resources/blob/master/nsh_sfc/Interaction%20between%20controller%20and%20nodes.png)

## Database
> Based on the database structure in [Service Function Chaining Application for Ryu SDN controller](https://github.com/abulanov/sfc_app)

![database1](https://github.com/destinysky/resources/blob/master/nsh_sfc/database1.png)
![database2](https://github.com/destinysky/resources/blob/master/nsh_sfc/database2.png)
![database3](https://github.com/destinysky/resources/blob/master/nsh_sfc/database3.png)

## Cooperation with VNF allocation model (Optional)
The allocation of VNFs can be input manually. It can also be allocated automatically by using VNF allocation model (Linear Programming approach or other algorithms).

![cooperation](https://github.com/destinysky/resources/blob/master/nsh_sfc/cooperation.png)


## Demonstration
### Brief:
#### Topology:
![Topology](https://github.com/destinysky/resources/blob/master/nsh_sfc/demo.png)

#### Service: 1→2, 3 → 4 → 5
#### Objective function: minimize the maximum number of VNFs allocated to each nodes
![Objective](http://latex.codecogs.com/gif.latex?\\min\\max_{n\in%20N}\\sum_{r\\in%20R}{\\sum_{k\\in%20K_r}{x_{n}^{rk}}})

*N* is the set of nodes. *R* is the set of SFCs. ![](http://latex.codecogs.com/gif.latex?K_r) is the set of VNFs in SFC *r*. ![](http://latex.codecogs.com/gif.latex?x_n^{rk}=1)  VNF *k* in SFC *r* is allocated to node *n*, 0 otherwise.

### Steps:

### Result:
#### Imgs:

#### Video:



