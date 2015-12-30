# encoding: utf-8

from collections import defaultdict


def count(data, res):
    f = open(data)
    for line in f.readlines():
        for w in line.split():
            res[w] += 1
    return res

if __name__ == "__main__":
    import os
    data = os.path.dirname(os.path.abspath(__file__)) + '/../data/testfile'
    res = defaultdict(int)
    count(data, res)
    print len(res)
    # for k, v in res.iteritems():
    #    print "{} -> {}".format(k, v)
