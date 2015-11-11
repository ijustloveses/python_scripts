# encoding: utf-8

'''Pipeline
    Some improvements after: http://www.dabeaz.com/Fcoroutines/Coroutines.pdf
    - coroutine decorator
    - catch GeneratorExit: 当自己被 close() 时，告诉下游的节点也 close()
'''

from contextlib import contextmanager


def coroutine(f):

    def start(*args, **kwargs):
        cr = f(*args, **kwargs)
        cr.next()
        return cr

    return start


@contextmanager
def close_on_exit(n):
    try:
        yield
    except GeneratorExit:
        n.close()


class StopPipeline(Exception):
    pass


class Pipeline(object):
    '''Chain stages together. Assumes the last is the consumer.'''

    def __init__(self, *args):
        c = Pipeline.C(args[-1])
        t = c
        for stg in reversed(args[1:-1]):
            s = Pipeline.S(stg, t)
            t = s
        p = Pipeline.P(args[0], t)
        self._pipeline = p

    def start(self, initial_state):
        try:
            self._pipeline.send(initial_state)
        except StopIteration:
            self._pipeline.close()

    @staticmethod
    @coroutine
    def P(f, n):
        '''Producer: only .send (and yield as entry point).'''
        state = (yield)  # get initial state
        with close_on_exit(n):
            while True:
                try:
                    res, state = f(state)
                except StopPipeline:
                    return
                n.send(res)

    @staticmethod
    @coroutine
    def S(f, n):
        '''Stage: both (yield) and .send.'''
        with close_on_exit(n):
            while True:
                r = (yield)
                n.send(f(r))

    @staticmethod
    @coroutine
    def C(f):
        '''Consumer: only (yield).'''
        # nothing to "close" here
        while True:
            r = (yield)
            f(r)


def produce((urls, visited, domain)):
    '''Given a state, produce a result and the next state.'''
    import urllib2
    import re

    nurls = len(urls)
    if nurls == 0:
        raise StopPipeline('No more urls')
    else:
        print 'Queue %d' % nurls

    url = urls.pop()
    doc = urllib2.urlopen(url).read()

    links = re.compile('href="(http.+?)"').findall(doc)
    urls.update([l for l in links if domain in l and l not in visited])
    visited.add(url)

    return (url, doc), (urls, visited, domain)


def stage((url, doc)):
    return (url, 'python' in doc.lower())


def consume((url, haskell)):
    if haskell:
        print 'Python mentioned in %s' % url


if __name__ == '__main__':
    p = Pipeline(
        produce,
        stage,
        consume,
    )
    urls = {'http://news.ycombinator.com'}
    domain = 'ycombinator.com'
    p.start((urls, set(), domain))
