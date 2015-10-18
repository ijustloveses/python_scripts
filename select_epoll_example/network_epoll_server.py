# encoding=utf-8

import socket
import select
import Queue

def create_server(ip, port, blocking=False, backlog=5):
    svr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    svr.setblocking(blocking)
    svr.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    svr_addr = (ip, port)
    svr.bind(svr_addr)
    svr.listen(backlog)
    return svr

def epoll_proc(svr):
    msg_queues = {}
    timeout = 20
    READ_ONLY = (select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR)
    READ_WRITE = (READ_ONLY | select.POLLOUT)
    poller = select.poll()
    poller.register(svr, READ_ONLY)

    # map file descriptors to socket obj
    fd_to_socket = {svr.fileno(): svr, }
    while True:
        print 'waiting for the next event'
        events = poller.poll(timeout)
        print "*" * 20
        print len(events)
        print events
        print "*" * 20
        for fd, flag in events:
            s = fd_to_socket[fd]
            if flag & (select.POLLIN | select.POLLPRI):
                # step 1. 客户端连接进来，给客户端连接加入只读监听
                if s is svr:
                    conn, client_addr = s.accept()
                    print "     Connection ", client_addr
                    conn.setblocking(False)
                    fd_to_socket[conn.fileno()] = conn
                    poller.register(conn, READ_ONLY)
                    msg_queues[conn] = Queue.Queue()
                else:
                    data = s.recv(1024)
                    # step 2. 客户端发送信息过来
                    if data:
                        print "     received %s from %s " % (data, s.getpeername())
                        msg_queues[s].put(data)
                        # 改为读写模式
                        poller.modify(s, READ_WRITE)
                    # step 5. 读不到数据了，那么关闭
                    else:
                        print "     closing ", s.getpeername()
                        poller.unregister(s)
                        s.close()
                        del msg_queues[s]
            elif flag & select.POLLHUP:
                print " Closing ", s.getpeername(), " (HUP)"
                poller.unregister(s)
                s.close()
            # 输出的 fd 准备好了
            elif flag & select.POLLOUT:
                try:
                    next_msg = msg_queues[s].get_nowait()
                except Queue.Empty:
                    # step 4. 没消息可发了，empty
                    print s.getpeername(), " queue empty"
                    poller.modify(s, READ_ONLY)
                else:
                    # step 3. echo back 消息给客户端
                    print "     sending %s to %s" % (next_msg, s.getpeername())
                    s.send(next_msg)
            elif flag & select.POLLERR:
                print "     exception on ", s.getpeername()
                poller.unregister(s)
                s.close()
                del msg_queues[s]

if __name__ == '__main__':
    epoll_proc(create_server('127.0.0.1', 10001))
