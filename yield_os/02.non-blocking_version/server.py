# encoding: utf-8

from socket import *
import oslike


def handle_client(client, addr):
    print("connection from %s" % addr)
    while True:
        yield oslike.ReadWait(client)
        data = client.recv(65536)
        if not data:
            break
        yield oslike.WriteWait(client)
        client.send(data)
    client.close()
    print("client closed")
    yield     # make it a generator/coroutine

def server(port):
    print("server starting")
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(("", port))
    sock.listen(5)
    while True:
        yield oslike.ReadWait(sock)
        client, addr = sock.accept()
        yield oslike.NewTask(handle_client(client, addr))

def alive():
    for i in range(30):
        print("alive !")
        yield

if __name__ == '__main__':
    sched = oslike.Scheduler()
    sched.new(alive())
    sched.new(server(45000))
    sched.mainloop()
