# -*- coding: utf-8 -*-
"""
Created on Fri May  3 00:24:53 2019

@author: destiny
"""

from pulp import *
import socket
import sys

nodes=5
ip=[]
requests=2
Kr=[2,3]
VNFid=[['1','2'],['3','4','5']]
VNFname=[['forward1','forward2'],['forward3','forward4','forward5']]
type_id='1'
group_id='1'
iftype='3'

folder='sfc_test'
portLis=50000


def send(msg,host,port):
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    except socket.error:
        print ('Failed to create socket')
        sys.exit()
    addr=(host,port)
    s.sendto(msg.encode('utf-8'),addr)
    s.close()


def do_lp(f2):

    x_rkn={}
    for i in range(int(len(R))):
        x_rkn.update(LpVariable.dicts("x",(R[i],K[i],Nodes),0,1,LpInteger))
    alpha=LpVariable("alpha", lowBound=0, upBound=max(Kr),cat='Integer')
    x_res=[[[] for _ in range(Kr[i]) ] for i in range(requests)]
    
    prob = LpProblem(folder, LpMinimize)
    
    prob += alpha,"(1)obj"

    for n in Nodes:
        prob += lpSum([lpSum([x_rkn[r][k][n] for k in K[int(r)-1]]) for r in R])<=alpha,"(1)"+n

    for n in Nodes:
        for r in R:
            prob += lpSum([x_rkn[r][k][n] for k in K[int(r)-1]])<=1,"(2)"+n+r
                   
    for r in R:
        for k in K[int(r)-1]:
            prob += lpSum([x_rkn[r][k][n] for n in Nodes]) ==1,"(3)"+r+k

    prob.writeLP("./"+folder+"/node.lp")

    prob.solve()#CPLEX(msg=False)
    f = open("./"+folder+"/node_out.txt", 'w')

    print ("Status:", LpStatus[prob.status], file=f)
    print ("Status:", LpStatus[prob.status])
    for v in prob.variables():
        print (v.name, "=", v.varValue, file=f)
        if (v.name.startswith("x") and int(v.varValue)==1):
            print (v.name, "=", v.varValue)
            print (v.name, "=", int(v.varValue), file=f2)
            name_temp=v.name.split('_')
            x_res[int(name_temp[1])-1][int(name_temp[2])-1]=int(name_temp[3])-1
    print ("Result = ", value(prob.objective), file=f)
    print ("Result = ", value(prob.objective))
    f.close()
    return x_res

#message:$$name,VNFid,type_id,group_id,iftype$$
def send_com(addr,VNFname,VNFid,type_id,group_id,iftype):
    msg='$$'+VNFname+','+VNFid+','+type_id+','+group_id+','+iftype+'$$'
    print(msg,addr,portLis)
    send(msg,addr,portLis)


if __name__ == '__main__':
    Nodes = [str(x) for x in list(range(1,nodes+1))]
    
    R = [str(x) for x in list(range(1,requests+1))]

    K=[]
    for i in range(int(len(R))):
        K.append([str(x+1) for x in list(range(int(Kr[i])))])

    for i in Nodes:
        ip.append('10.0.0.'+i)
    
    f2 = open("./"+folder+"/"+folder+".txt", 'w')

    res=do_lp(f2)
    for r in range(requests):
        for k in range(Kr[r]):
            loc=int(res[r][k])
            send_com(ip[loc],VNFname[r][k],VNFid[r][k],type_id,group_id,iftype)
            
    f2.close()
