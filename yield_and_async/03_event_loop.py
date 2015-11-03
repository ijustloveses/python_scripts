# encoding: utf-8

"""
    Implement a service which could handle time-based tasks,
    normal tasks, and read instruction from stdin

    Python 3 only
"""

from bisect import insort
from collections import deque
from functools import partial
from time import time
import selectors    # Python 3 only
import sys
import types


def fib(n):
    if n < 2:
        yield n
    else:
        a = yield fib(n - 1)
        b = yield fib(n - 2)
        yield a + b


class sleep_for_seconds(object):
    def __init__(self, wait_time):
        self._wait_time = wait_time


class EventLoop(object):
    def __init__(self, *tasks):
        self._running = False
        self._selector = selectors.DefaultSelector()
        self._tasks = deque(tasks)          # Queue of functions scheduled to run
        self._tasks_waiting_on_stdin = []   # (coroutine, stack) pair of tasks
        self._timers = []
        self._selector.register(sys.stdin, selectors.EVENT_READ)  # polling stdin

    def schedule(self, coroutine, value=None, stack=(), when=None):
        """
            Schedule a coroutine task to run, with value to be sent to it
            and the stack containing the coroutines that are waiting for the value
            yielded by this coroutine
        """
        'task is wrapped into a partial function, but will not call it now'
        task = partial(self.resume_task, coroutine, value, stack)
        'just put it in timers or normal tasks queue'
        if when:
            insort(self._timers, (when, task))
        else:
            self._tasks.append(task)

    def resume_task(self, coroutine, value=None, stack=()):
        """
            Actual tasks handling function
            It will send value to coroutine and get result from coroutine
            then schedule new task based on result type
        """
        result = coroutine.send(value)
        if isinstance(result, types.GeneratorType):
            'result is a generator, which is actually a new coroutine to be scheduled'
            self.schedule(result, None, (coroutine, stack))
        elif isinstance(result, sleep_for_seconds):
            'result is a time-based event, reschedule the result'
            self.schedule(coroutine, None, stack, time() + result._wait_time)
        elif result is sys.stdin:
            'if coroutine yields sys.stdin, it is waiting on stdin, so put is on waiting list'
            self._tasks_waiting_on_stdin.append((coroutine, stack))
        elif stack:
            'if not result to reschedule, test if there are still coroutines in stack'
            self.schedule(stack[0], result, stack[1])

    def stop(self):
        self._running = False

    def do_on_next_tick(self, func, *args, **kwargs):
        'put the task at the first position of the task queue'
        self._tasks.appendleft(partial(func, *args, **kwargs))

    def run_forever(self):
        self._running = True
        while self._running:
            'check stdin first'
            for key, mask in self._selector.select(0):
                line = key.fileobj.readline().strip()
                for task, stack in self._tasks_waiting_on_stdin:
                    'schedule tasks to run'
                    self.schedule(task, line, stack)
                self._tasks_waiting_on_stdin.clear()

            'check task queue, one task at one tick from left to right'
            if self._tasks:
                task = self._tasks.popleft()
                task()

            'time schedule tasks, which are sorted in self._timers'
            while self._timers and self._timers[0][0] < time():
                task = self._timers[0][1]
                'so the next iteration, the next task will be check'
                del self.timers[0]
                task()
        self._running = False


def print_every(message, interval):
    """
        Task coroutine which will generate sleep_for_seconds obj repeatly
    """
    while True:
        print("{} - {}".format(int(time()), message))
        yield sleep_for_seconds(interval)


def read_input(loop):
    """
        Task coroutine to read new lines from stdin, and calculate fib with input number
        With the yield style, fib(n) will be scheduled inside the EventLoop
    """
    while True:
        line = yield sys.stdin
        if line == 'exit':
            loop.do_on_next_tick(loop.stop)
            continue
        n = int(line)
        fib_n = yield fib(n)
        print("fib({}) = {}".format(n, fib_n))


def main():
    loop = EventLoop()
    hello_task = print_every('Hello', 3)
    fib_task = read_input(loop)
    loop.schedule(hello_task)
    loop.schedule(fib_task)
    loop.run_forever()


if __name__ == '__main__':
    main()
