# encoding: utf-8

"""
    Multi-Radix Number:
        input: [2, 1, 3]
        output:
            [0, 0, 0]
            [0, 0, 1]
            [0, 0, 2]
            [1, 0, 0]
            [1, 0, 1]
            [1, 0, 2]
"""

from itertools import product


def multiradix_product(M):
    """ Method 1. using itertools.product, baseline """
    return product(*(range(x) for x in M))


def multiradix(M, a, i):
    """
        Method 2. recursive - divide & conquer
        M: input list
        a: [0] * len(M), the list to fill
        i: 0 ~ n-1, scale of the sub-problem
    """
    if i < 0:
        " start point to fill a, from the 1st element "
        yield a
    else:
        " iterate the result from sub-problem "
        for _ in multiradix(M, a, i - 1):
            " a[0] ~ a[i-1] have been filled "
            for x in range(M[i]):
                a[i] = x
                yield a


def multiradix_recursive(M):
    n = len(M)
    a = [0] * n
    " Only handle those lists yield from multiradix(M, a, n - 1) "
    return multiradix(M, a, n - 1)


def multiradix_iterative(M):
    """
        Method 3. iterative
        start scanning from right to left until we find an index in a
        that we can increment, do the incrementation, and then set
        everything to the right of that index to 0

        Working like a clock!!!
    """
    n = len(M)
    a = [0] * n
    while True:
        yield a
        " reset k to the last postion everytime "
        k = n - 1
        " whenever a[k] == M[k] - 1, the value on the position after than k are always 0"
        while a[k] == M[k] - 1:
            a[k] = 0
            k -= 1
            if k < 0:
                " last lexicographic item "
                return
        " before reaching the limit, just incr a[k] "
        a[k] += 1


def multiradix_coroutine(M):
    """
        Method 4. Acting as iterative method except using coroutine.
        Fact is that this method is the decomposition of iterative method.
    """
    n = len(M)
    a = [0] * n
    lead = troll(M, a, n - 1)
    yield a
    " In fact, it is just like the outer loop in iterative method, and always call the last troll "
    while next(lead):
        yield a


def nobody():
    """
        The 1st troll in the line
    """
    while True:
        yield False


def troll(M, a, i):
    """
        Generator of booleans, and manipulate a during generating
        Imaging a line of n+1 trolls. Each troll, with the exception of the first troll holds
        a number in his hand. The trolls will behave in the following manner:
        When a troll is poked, if the number in his hand is strictly less than mi−1
        (meaning the number can be increased) he simply increments the number and yells out "done".
        If the number in his hand is equal to mi−1 then he changes the number to 0 and
        then pokes the previous troll without yelling anything. And the 1st troll always yell "last".
    """
    "Each troll creates the troll previous to it in line, until we get to troll number 0 "
    previous = troll(M, a, i - 1) if i > 0 else nobody()
    " just like the inner loop in iterative method "
    while True:
        if a[i] == M[i] - 1:
            a[i] = 0
            yield next(previous)
        else:
            a[i] += 1
            yield True


if __name__ == '__main__':
    M = [2, 1, 3]
    print "method product:"
    for i in multiradix_product(M):
        print i
    print "method recursive:"
    for i in multiradix_recursive(M):
        print i
    print "method iterative:"
    for i in multiradix_iterative(M):
        print i
    print "method coroutine:"
    for i in multiradix_coroutine(M):
        print i
