# encoding: utf-8

import copy


def Memento(obj, deep=False):
    # state = copy.deepcopy(obj.__dict__) if deep else copy.copy(...)
    state = (copy.copy, copy.deepcopy)[bool(deep)](obj.__dict__)

    def Restore():
        obj.__dict__.clear()
        obj.__dict__.update(state)
    return Restore


class Transaction:
    """ syntactic sugger for Memento closure
        用来包装 Objects，提供备忘和恢复的手段
    """
    deep = False
    def __init__(self, *targets):
        self.targets = targets
        self.Commit()

    # 调用 Commit，则备忘 targets
    def Commit(self):
        self.states = [Memento(target, self.deep) for target in self.targets]

    # 调用 rollback，则恢复 targets
    def Rollback(self):
        for state in self.states:
            state()


class transactional(object):
    """ 这个用来包装 Action, 每次调用之前先备忘，如果异常自动恢复 """
    def __init__(self, method):
        self.method = method

    def __get__(self, obj, T):
        def transaction(*args, **kwargs):
            state = Memento(obj)
            try:
                return self.method(obj)
            except:
                state()
                raise
        return transaction


if __name__ == "__main__":
    class NumObj(object):
        def __init__(self, value):
            self.value = value
        def __repr__(self):
            return '<%s: %r>' % (self.__class__.__name__, self.value)
        def Inc(self):
            self.value += 1
        @transactional
        def DoStuff(self):
            self.value = 'string instead of number'
            self.Inc()    # 这里将会失败，字符串 += 1，看是否会恢复 rollback

    """ 下面测试 Transaction，需要手动写 try except """
    n = NumObj(-1)
    print n
    t = Transaction(n)
    for i in range(3):
        n.Inc()
        print n
    t.Commit()
    print 'commited now'
    try:
        for i in range(3):
            n.Inc()
            print n
        n.value += 'xxxxx'    # 这里将会失败
        print n
    except:
        t.Rollback()
        print "rollbacked now"
    print n

    """ 下面测试 transactional，这里也写了 try except，不过不是为了恢复数据，
        只是因为 transactional 在恢复数据之后，会自动重新抛出异常
    """
    print 'do stuff'
    try:
        n.DoStuff()
    except:
        print 'do stuff failed'
        import traceback
        traceback.print_exc(0)
        pass
    print n
