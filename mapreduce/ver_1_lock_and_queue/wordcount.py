# encoding: utf-8

from mapreduce import MapReduce
import Queue


class WordCount(MapReduce):
    def __init__(self):
        super(WordCount, self).__init__()

    def parse(self):
        f = open(self.data)
        q = Queue.Queue()
        for line in f.readlines():
            q.put((line, None))
        f.close()
        return q

    def map(self, k, v):
        words = []
        for w in k.split():
            words.append((w, 1))
        return words

    def reduce(self, k, l):
        return (k, sum(l))


if __name__ == "__main__":
    import sys
    import os
    num = 1
    if len(sys.argv) > 1:
        num = int(sys.argv[1])
    wc = WordCount()
    wc.data = os.path.dirname(os.path.abspath(__file__)) + '/../data/testfile'
    wc.workerNum = num
    q = wc.run()
    uniq = 0
    while not q.empty():
        q.get()
        uniq += 1
    print "uniq: %d" % uniq
