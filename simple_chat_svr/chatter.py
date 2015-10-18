# encoding: utf-8
import socket
import sys
import threading
import time

class User:
    def __init__(self, skt, name='none'):
        self.skt = skt
        self.name = name
    def send_msg(self, msg):
        self.skt.send(msg)
    def logout(self):
        self.skt.close()

userlist = []

""" server side , 新建一个 thread 来处理用户的输入 """

def hand_user_con(usr):
    try:
        isnormal = True
        while isnormal:
            data = usr.skt.recv(1024)
            time.sleep(1)
            msg = data.split('|')
            if msg[0] == 'login':
                print 'user [%s] login' % msg[1]
                usr.name = msg[1]
                userlist.append(usr)
                notice_others(usr)
            elif msg[0] == 'talk':
                print 'user [%s] to [%s]: %s' % (usr.name, msg[1], msg[2])
                send_msg(usr.name, msg[1], msg[2])
            elif msg[0] == 'exit':
                print 'user [%s] left' % usr.name
                isnormal = False
                usr.logout()
                userlist.remove(usr)
    except:
        isnormal = False

def notice_others(usr):
    for other in userlist:
        if other.name != usr.name:
            other.skt.send('login|' + usr.name)

def send_msg(sender_name, receiver_name, msg):
    for usr in userlist:
        if usr.name == receiver_name:
            usr.skt.send('talk|' + sender_name + '|' + msg)
            break

def server_run():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 9999))
    s.listen(5)
    while True:
        sock, addr = s.accept()
        user = User(sock)
        t = threading.Thread(target=hand_user_con, args=(user,))
        t.start()
    s.close()


""" client side , 新建一个 thread 来处理 server 的消息 """

def receive_msg(name, skt):
    skt.send('login|' + name)
    while True:
        data = skt.recv(1024)
        msg = data.split('|')
        if msg[0] == 'login':
            print '%s has logged in' % msg[1]
        elif msg[0] == 'talk':
            print 'receive msg [from %s]: %s' % (msg[1], msg[2])

def client_run():
    try:
        print 'Please input your name:'
        name = raw_input()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 9999))
        t = threading.Thread(target=receive_msg, args=(name, s))
        t.start()
    except:
        sys.exit(1)
    while True:
        print 'Please input you message: talk|<to>|<msg>:'
        msg = raw_input()
        if msg == 'exit':
            s.send('exit')
            break
        else:
            s.send(msg)
    s.close()
