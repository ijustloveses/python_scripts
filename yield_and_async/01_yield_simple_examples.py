# encoding: utf-8

from collections import defaultdict as dd


def simple_generator():
    def add_func(a, b):
        return a + b

    def add_coroutine(a, b):
        yield a + b

    x = add_func(1, 2)
    print x

    adder = add_coroutine(1, 2)
    x = next(adder)
    print x

    try:
        x = next(adder)
    except:
        print 'Exception raised when generator exsaust'


def fib_generator():
    def fib():
        a, b = 0, 1
        while True:
            yield b
            a, b = b, a + b

    f = fib()
    print(next(f))
    print(next(f))
    print(next(f))
    print(next(f))
    print(next(f))


def recursive_generator():
    """
        generators can be recursive, and be used inside for loops
    """
    def postorder(tree):
        if not tree:
            return
        """
            resursively used in for loop
            in Python 3, below lines could be simplified as:
                yield from postorder(tree['left'])
        """
        for x in postorder(tree['left']):
            yield x
        for x in postorder(tree['right']):
            yield x
        " postorder: left -> right -> parent "
        yield tree['value']

    " build a tree representing (1 + 3) * (4 - 2) "
    tree = lambda: dd(tree)
    T = tree()
    T['value'] = '*'
    T['left']['value'] = '+'
    T['left']['left']['value'] = '1'
    T['left']['right']['value'] = '3'
    T['right']['value'] = '-'
    T['right']['left']['value'] = '4'
    T['right']['right']['value'] = '2'

    postfix = ' '.join(str(x) for x in postorder(T))
    ' would output: 1 3 + 4 2 - * '
    print postfix


if __name__ == '__main__':
    simple_generator()
    fib_generator()
    recursive_generator()
