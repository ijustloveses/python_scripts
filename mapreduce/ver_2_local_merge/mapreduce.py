# encoding: utf-8

from __future__ import with_statement
import threading
import Queue
import operator


class SynchronizedDict(dict):
    def __init__(self, *args, **kwargs):
        super(SynchronizedDict, self).__init__(*args, **kwargs)
        self.lock = threading.Lock()

    def __getitem__(self, k):
        """
            xx[yy]
        """
        with self.lock:
            return super(SynchronizedDict, self).__getitem__(k)

    def __setitem__(self, k, v):
        """
            xx[yy] = zz
        """
        with self.lock:
            return super(SynchronizedDict, self).__setitem__(k, v)

    def __contains__(self, k):
        """
            xx.contain(yy)
        """
        with self.lock:
            return super(SynchronizedDict, self).__contains__(k)

    def get(self, k, default=None):
        with self.lock:
            return super(SynchronizedDict, self).get(k, default=default)

    def items(self):
        with self.lock:
            return super(SynchronizedDict, self).items()

    def set_append(self, k, v):
        """
            这里要求值是个 list
        """
        with self.lock:
            if super(SynchronizedDict, self).__contains__(k):
                super(SynchronizedDict, self).__setitem__(k, super(SynchronizedDict, self).__getitem__(k) + [v, ])
            else:
                super(SynchronizedDict, self).__setitem__(k, [v, ])


class MapReduce(object):
    def __init__(self):
        self.workerNum = 1
        self.data = None
        self.sdict = SynchronizedDict()
        self.mapq = Queue.Queue()
        self.mergeq = Queue.Queue()
        self.reduceq = Queue.Queue()

    def parse(self):
        pass

    def map(self, k, v):
        """
            (k, v) => [(k1, v1), (k2, v2), ..]
        """
        pass

    def local_merge(self, cache, k, v):
        if k in cache:
            cache[k].append(v)
        else:
            cache[k] = [v, ]

    def merge(self, k, v):
        self.sdict.set_append(k, v)

    def local_reduce(self, k, l):
        """
            By default, local_reduce is exactly the same as reduce
        """
        return self.reduce(k, l)

    def reduce(self, k, l):
        pass

    def process_map(self):
        """
            self.mapq holds [(k1, v1), (k2, v2), ...]
        """
        def worker():
            local_res = {}
            while not self.mapq.empty():
                k, v = self.mapq.get()
                for k2, v2 in self.map(k, v):
                    self.local_merge(local_res, k2, v2)
            for k, l in local_res.iteritems():
                v = self.local_reduce(k, l)
                self.mergeq.put(self.local_reduce(k, l))

        threads = []
        for i in range(self.workerNum):
            workerThread = threading.Thread(target=worker)
            workerThread.setDaemon(True)
            workerThread.start()
            threads.append(workerThread)
        for th in threads:
            th.join()

    def process_merge(self):
        """
            self.mergeq holds [(k1, v1), (k2, v2), ...]
        """
        def worker():
            while not self.mergeq.empty():
                k, v = self.mergeq.get()
                self.merge(k, v)
                self.mergeq.task_done()

        for i in range(self.workerNum):
            workerThread = threading.Thread(target=worker)
            workerThread.setDaemon(True)
            workerThread.start()
        self.mergeq.join()

        outputList = sorted(self.sdict.items(), key=operator.itemgetter(0))
        for v in outputList:
            self.reduceq.put(v)

    def process_reduce(self):
        """
            self.reduceq holds [(k1, list of v1), (k2, list of v2), ...]
        """
        outqueue = Queue.Queue()

        def worker():
            while not self.reduceq.empty():
                k, l = self.reduceq.get()
                outqueue.put(self.reduce(k, l))
                self.reduceq.task_done()

        for i in range(self.workerNum):
            workerThread = threading.Thread(target=worker)
            workerThread.setDaemon(True)
            workerThread.start()
        self.reduceq.join()
        return outqueue

    def run(self):
        self.mapq = self.parse()
        self.process_map()
        self.process_merge()
        return self.process_reduce()
