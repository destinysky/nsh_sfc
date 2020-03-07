import socket

portLis=50001
def send(msg,host,port):
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    addr=(host,port)
    s.sendto(msg.encode('utf-8'),addr)
    s.close()

if __name__ == '__main__':
    msg=input('Please input message:')
    addr=input('Please input address:')
    send(msg,addr,portLis)
