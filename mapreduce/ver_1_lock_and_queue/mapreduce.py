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

    def parse(self):
        pass

    def map(self, k, v):
        """
            (k, v) => [(k1, v1), (k2, v2), ..]
        """
        pass

    def _merge(self, k, v):
        self.sdict.set_append(k, v)

    def reduce(self, k, l):
        pass

    def process_queue(self, inqueue, selector):
        """
            inqueue holds [(k1, v1), (k2, v2), ...]
        """
        print "running %s ..." % selector
        outqueue = Queue.Queue()

        def worker():
            while not inqueue.empty():
                k, v = inqueue.get()
                if selector == "map":
                    returnList = self.map(k, v)
                    for res in returnList:
                        outqueue.put(res)
                elif selector == "reduce":
                    outqueue.put(self.reduce(k, v))
                elif selector == "merge":
                    self._merge(k, v)
                else:
                    raise Exception("Invalid selector: %s" % selector)
                inqueue.task_done()   # used along with join(), decrease count

        for i in range(self.workerNum):
            workerThread = threading.Thread(target=worker)
            workerThread.setDaemon(True)
            workerThread.start()

        inqueue.join()

        if selector == "merge":
            outputList = sorted(self.sdict.items(), key=operator.itemgetter(0))
            for v in outputList:
                outqueue.put(v)

        return outqueue

    def run(self):
        inqueue = self.parse()
        for selector in ("map", "merge", "reduce"):
            inqueue = self.process_queue(inqueue, selector)
        return inqueue
