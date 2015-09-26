# encoding=utf-8
import socket

messages = ['this is a message',
            'it will be sent',
            'in parts ']
print 'connecting to the server'
server_addr = ('127.0.0.1', 10001)
socks = []

# create 5 client sockets
for i in range(5):
    socks.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))

for s in socks:
    s.connect(server_addr)

for msg in messages:
    counter = 0
    for s in socks:
        counter += 1
        message = msg + " @client_" + str(counter)
        print "     %s sending %s" % (s.getpeername(), message)
        s.send(message)
    for s in socks:
        data = s.recv(1024)
        print "     %s recv %s" % (s.getpeername(), data)
        if not data:
            print "     closing socket ", s.getpeername()
            s.close()
