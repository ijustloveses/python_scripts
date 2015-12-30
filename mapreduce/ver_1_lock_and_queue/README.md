refer
======
https://github.com/yangjuven/MapReduce

workflow
=========
parse() 从原始数据得到一组 (k, v)，并存到 Queue 中

map 过程从 Queue 中获取 (k, v)，对每对儿 k, v 调用 map() 函数，并输出新的一组 (k, v)，保存到新的 Queue 中

merge 过程从 map 过程返回的 Queue 中获取 (k, v), 并根据 k 把 v 组成一个列表，放到一个 dict 中。

由于可能有多个 workers，故此实现了 SynchronizedDict 用来保存合并对象。

同步机制使用了锁，故此其实会比较慢，上锁解锁开销都不小。

最后把整理好的 (k, (list of v's)) 保存到一个新的 Queue 中

reduce 过程从 merge 过程返回的 Queue 中获取 (k, v), 其中 v 其实是一组 value 的列表，并调用 reduce() 函数得到最终的 k 的结果，并保存到新的 Queue 中

注意：
1. 由于 merge 过程有锁，故此效率不会很高；其实应该把 merge 过程 localize 本地化到 worker 中进行，最后对每个 worker 的最终结果做一次 merge 即可，效率会高很多。
2. parse/map/merge/reduce 过程都是相互独立的，不会交互运行；每个过程倒是可以使用多个 workers 来运行；每个过程最终都得到一个新的 Queue 以供后续过程来使用。
3. 由 2 可知，其实整个过程仍然是 batch 运行，而不是真正的 streaming 流式过程。

example
=========
test data
```
1 2 3 4 5
2 3 4 5
3 4 5
4 5
5
```

parse() => [("1 2 3 4 5", None), ("2 3 4 5", None), ("3 4 5", None), ("4 5", None), ("5", None)]

map 过程 => [("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("3", 1), ("4", 1), ("5", 1), ("4", 1), ("5", 1), ("5", 1)]

merge 过程 => [("1", [1]), ("2", [1, 1]), ("3", [1, 1, 1]), ("4", [1, 1, 1, 1]), ("5", [1, 1, 1, 1, 1])]

reduce 过程 => [("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)]
