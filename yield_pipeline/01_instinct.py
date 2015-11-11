# encoding: utf-8

import time

N = 0


def p(n):
    """
        producer，一旦被 next 激活，就陷入循环
        每秒增加全局变量 N，并 send 出去
    """
    def _f():
        global N
        N += 1
        time.sleep(1)
        return N

    yield    # to start, call next()
    while True:
        n.send(_f())


def s(n):
    """
        stage，它始终在循环状态，先阻塞等待外界的 send，
        然后把结果+1，再 send 出去
    """
    def _f(x):
        print "stage ", x
        return x + 1

    while True:
        r = (yield)
        n.send(_f(r))


def c():
    """
        consumer，始终再循环状态，先阻塞等待外界的 send
        然后打印出接收的值
    """
    def _f(x):
        print "consume ", x

    while True:
        r = (yield)
        _f(r)


def pipeline(*args):
    """
        pipeline，第一个是 producer，最后一个是 consumer
        中间都是 stage，其中 producer & stage 都会记录链条的下一个接受者
        从 consumer 开始，倒着初始化，每次初始化使用上次已初始化的部件为参数
        并调用 next() 进行激活，返回最后的一个部件，也就是 producer
    """
    c = args[-1]()
    c.next()
    t = c
    for S in reversed(args[:-1]):
        s = S(t)
        s.next()
        t = s
    return t


if __name__ == '__main__':
    p = pipeline(p, s, s, s, c)
    """ 如果第 19 行 yield 注释掉，那么就不需要下面这行来启动了 """
    p.next()     # to start
