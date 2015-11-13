# encoding: utf8

import time
import threading
import pprint


class CountDownLatch:
    def __init__(self, count=1):
        self.count = count
        self.lock = threading.Condition()    # 内置了一把锁

    def countDown(self):
        # 锁定内置锁
        self.lock.acquire()
        self.count -= 1
        if self.count <= 0:
            # 通知等待的线程倒数结束
            self.lock.notifyAll()
        # 开锁
        self.lock.release()

    def await(self):
        # 上锁
        self.lock.acquire()
        while self.count > 0:
            # 如果倒数未结束，则开锁并挂起
            # 被唤醒后会重新上锁
            self.lock.wait()
        # 开锁
        self.lock.release()


class WorkerThread(threading.Thread):
    latch = None
    count = 0
    method = None

    def __init__(self, latch, count, method):
        threading.Thread.__init__(self)
        self.latch = latch
        # count 是一次 countdown 中 method 被运行多少次, 和 latch's count 无关
        self.count = count
        self.method = method

    def run(self):
        while self.count > 0:
            self.method()
            self.count -= 1
        self.latch.countDown()


class MyPrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if isinstance(object, unicode):
            return (object.encode('utf8'), True, False)
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


class BatchRunner(object):
    def __init__(self, methods, count):
        self.methods = methods
        # 每个任务要被调用的次数
        self.count = count
        # len(self.methods) 个任务要执行，故此需要倒数相等的次数
        self.latch = CountDownLatch(len(self.methods))

    def run(self):
        start = int(time.time())
        for method in self.methods:
            # 每个任务分配一个线程，完成 count 次调用后倒数一下
            task = WorkerThread(self.latch, self.count, method)
            task.setDaemon(True)
            task.start()
        # 等待倒数完毕，之前一致挂起
        self.latch.await()
        end = int(time.time())
        elapsed = end - start
        print ('%d threads, %d calls per thread, cost time: %d seconds' % (len(self.methods), self.count, elapsed))


if __name__ == '__main__':
    def task1():
        print "----->"

    def task2():
        print "            <-----"

    methods = [task1, task2]
    br = BatchRunner(methods, 5)
    br.run()
