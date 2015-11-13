from threading import Thread
from collections import deque
from threading import RLock
from threading import Condition


class Producer(Thread):
    def __init__(self, queue, lock, cond):
        Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        self.cond = cond

    def run(self):
        while True:
            # 先上锁
            self.lock.acquire()
            while len(self.queue) == self.queue.maxlen:    # python2.7 required
                # 如果已满，释放锁，并挂起等待空位
                self.cond.wait()
            # 若未满，或者被唤醒并重新加锁，那么append
            print "produce:", self.queue.appendleft('production')
            # 然后通知 consumer 有货了
            self.cond.notify_all()
            # 释放锁
            self.lock.release()


class Consumer(Thread):
    def __init__(self, queue, lock, cond):
        Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        self.cond = cond

    def run(self):
        while True:
            self.lock.acquire()
            while len(self.queue) == 0:
                self.cond.wait()
            print "consume:", self.queue.pop()
            self.cond.notify_all()
            self.lock.release()

if __name__ == '__main__':
    lock = RLock()
    cond = Condition(lock)    # 配合 lock 使用
    queue = deque('', 3)
    Producer(queue, lock, cond).start()
    Consumer(queue, lock, cond).start()
