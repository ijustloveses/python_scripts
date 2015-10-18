# encoding=utf-8

import select
import socket
import Queue


def create_server(sip, port, blocking=False, backlog=5):
    svr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    svr.setblocking(blocking)
    svr.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    svr_addr = (sip, port)
    svr.bind(svr_addr)
    svr.listen(backlog)
    return svr


def select_proc(svr, timeout=20):
    inputs = [svr]
    outputs = []
    msg_queues = {}

    while inputs:
        print 'waiting for next event'
        readable, writable, exceptional = select.select(inputs, outputs, inputs, timeout)
        if not (readable or writable or exceptional):
            print 'Time out !'
            break
        for s in readable:
            # 如果 server 读到 client 连接，对应 client_sock.connect
            if s is svr:
                # 接受连接，获取 client addr (step 1.)
                connection, client_addr = s.accept()
                print "     connection from ", client_addr
                connection.setblocking(0)
                # 同时开始读取 client
                inputs.append(connection)
                # 并创建消息队列
                msg_queues[connection] = Queue.Queue()
            # 否则，如果是 client 收到服务器的回复消息
            else:
                # 接收到 client 的消息 (step 2.)
                data = s.recv(1024)
                if data:
                    print "     received ", data, " from ", s.getpeername()
                    msg_queues[s].put(data)
                    # 监听该 client 的输出消息
                    if s not in outputs:
                        outputs.append(s)
                # 如果再也收不到消息，那么是关闭，善后  (step 5.)
                else:
                    print "     closing ", client_addr
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()
                    del msg_queues[s]
        # 发往 client 的输出，准备完毕
        for s in writable:
            try:
                # 如果 queue 中有消息，那么发送到 client (step 3.)
                next_msg = msg_queues[s].get_nowait()
            except Queue.Empty:
                # 如果没有消息了，那么打印空 (step 4.)
                print "     ", s.getpeername(), " queue empty"
                outputs.remove(s)
            else:
                print "     sending ", next_msg, " to ", s.getpeername()
                s.send(next_msg)
        # 异常
        for s in exceptional:
            print "     exception condition on ", s.getpeername()
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del msg_queues[s]

if __name__ == "__main__":
    select_proc(create_server('127.0.0.1', 10001))
