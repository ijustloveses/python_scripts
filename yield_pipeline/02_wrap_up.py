# encoding: utf-8

"""
    和 01 的概念完全相同，只是做了简单的包装和重构，主要是：
    1. producer 接收外界传入的初始值了，见 Pipeline.P() 中的 state = (yield)
    2. producer, stage & consumer 的处理函数不再内部写死，而是作为 init 函数由外部定义
    3. state 只在 producer 中被改变和维护，由 producer 发给 stage 的是 producer 的内部函数调用结果
    和 01 一样，仍然是 producer & stage 都内部保存下一个节点，可以说是强耦合
"""

class StopPipeline(Exception):
    pass


class Pipeline(object):
    '''Chain stages together. Assumes the last is the consumer.'''
    def __init__(self, *args):
        c = Pipeline.C(args[-1])
        c.next()
        t = c
        for stg in reversed(args[1:-1]):
            s = Pipeline.S(stg, t)
            s.next()
            t = s
        p = Pipeline.P(args[0], t)
        p.next()
        self._pipeline = p

    def start(self, initial_state):
        try:
            self._pipeline.send(initial_state)
        except StopIteration:
            self._pipeline.close()

    @staticmethod
    def P(f, n):
        '''Producer: only .send (and yield as entry point).'''

        state = (yield)  # get initial state
        while True:
            try:
                res, state = f(state)
            except StopPipeline:
                return
            n.send(res)

    @staticmethod
    def S(f, n):
        '''Stage: both (yield) and .send.'''

        while True:
            r = (yield)
            n.send(f(r))

    @staticmethod
    def C(f):
        '''Consumer: only (yield).'''

        while True:
            r = (yield)
            f(r)


def produce(state):
    '''Given a state, produce a result and the next state.'''
    import time
    if state == 3:
        raise StopPipeline('Enough!')
    time.sleep(1)
    return state, state + 1


def stage(x):
    print 'Stage', x
    return x + 1


def consume(x):
    print 'Consumed', x


if __name__ == '__main__':
    p = Pipeline(
        produce,
        stage,
        stage,
        stage,
        consume,
    )
    initial_state = 0
    p.start(initial_state)
