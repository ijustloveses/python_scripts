# encoding=utf-8
import gevent.monkey
gevent.monkey.patch_socket()

import gevent
import urllib2
import json

def fetch(pid):
    response = urllib2.urlopen('http://baidu.com')
    result = response.read()
    print ('Process %s' % (pid))
    return 

def synchronous():
    for i in range(1, 10):
        fetch(i)

def asynchronous():
    threads = []
    for i in range(1, 10):
        threads.append(gevent.spawn(fetch, i))
    gevent.joinall(threads)

print('Synchronous:')
synchronous()

print('Asynchronous:')
asynchronous()


from multiprocessing.dummy import Pool as ThreadPool
urls = ['http://baidu.com', 'http://www.newsmth.net', 'http://www.sina.com.cn']
pool = ThreadPool()
print "pooling:"
results = pool.map(urllib2.urlopen, urls)
pool.close()
pool.join()

