workflow
=========
parse() 从原始数据得到一组 (k, v)，并存到 map_queue 中

map 过程从 map_queue 中获取 (k, v)，对每对儿 k, v 调用 map() 函数，并输出新的一组 (k, v)；然后使用 local_merge 来把该 map worker 中处理的 k, v merge 到本地的 dict 数据结构中

local_merge 类似 ver_1 中的 merge，但是不必使用 SynchronizedDict，因为是 worker 自己单独处理，按 k 分组，把该 k 对应的所有 v 放到一个 list 中

当 map_queue 已空，也就是 local_merge 完成，把 merge 得到的本地 dict 中的本地结果进行 local_reduce，每个 k 得到一个 reduce 的结果，放到 merge_queue 中

merge 过程从 merge_queue 中获取 (k, v), 并根据 k 把 v 组成一个列表，放到一个 dict 中。

由于可能有多个 workers，故此实现了 SynchronizedDict 用来保存合并对象。

同步机制使用了锁，会由于上锁解锁影响效率，但是由于是作用在已经做了 local_merge & local_reduce 的结果中，故此效率上的损失降到了很小

最后把整理好的 (k, (list of v's)) 保存到一个 reduce_queue 中

reduce 过程从 reduce_queue 中获取 (k, v), 其中 v 其实是一组 value 的列表，并调用 reduce() 函数得到最终的 k 的结果，并保存到新的 Queue 中

注意：

1. 虽然仍然是有锁，但是由于锁只作用在经过本地处理后的结果集上， 故此效率影响不大；尤其是对于数据量远远大于 key 的数量的 case，本地结果集会很小，锁的影响就很小
2. parse/map/merge/reduce 过程仍然是相互独立的，不会交互运行；每个过程倒是可以使用多个 workers 来运行，仍然不是真正的 streaming 流式过程

貌似，map-reduce 要有效率(做 local 处理)，又要 streaming 本身似乎就是有矛盾的啊 ...


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

假设有两个 map workers

map_1 过程 => [("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1)]

map_2 过程 => [("3", 1), ("4", 1), ("5", 1), ("4", 1), ("5", 1), ("5", 1)]

local_merge1 => [("1", [1]), ("2", [1, 1]), ("3", [1, 1]), ("4", [1, 1]), ("5", [1, 1])]

local_merge2 => [("3", [1]), ("4", [1, 1]), ("5", [1, 1, 1])]

local_reduce1 => [("1", 1), ("2", 2), ("3", 2), ("4", 2), ("5", 2)]

local_reduce2 => [("3", 1), ("4", 2), ("5", 3)]

虽然是两个 merge worker，但是都往共享的 SynchronizedDict 中写，故此最后是一个结果

merge 过程 => [("1", [1]), ("2", [2]), ("3", [2, 1]), ("4", [2, 2]), ("5", [2, 3])]

reduce 过程 => [("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)]


code review
=============

process_merge 中，有如下的代码：
``` python
    def process_merge(self):
        def worker():
            while not self.mergeq.empty():
                k, v = self.mergeq.get()
                self.merge(k, v)
                self.mergeq.task_done()

        for i in range(self.workerNum):
            workerThread = threading.Thread(target=worker)
            workerThread.setDaemon(True)
            workerThread.start()
        self.mergeq.join()

        outputList = sorted(self.sdict.items(), key=operator.itemgetter(0))
        for v in outputList:
            self.reduceq.put(v)
```
join() 保持阻塞状态，直到处理了队列中的所有项目为止。

在将一个项目添加到该队列时，未完成的任务的总数就会增加。

当使用者线程调用 task_done() 以表示检索了该项目、并完成了所有的工作时，那么未完成的任务的总数就会减少。

当未完成的任务的总数减少到零时，join() 就会结束阻塞状态。

故此，上述代码中，当 merge_queue 空掉时，主线程才会运行到下面的排序 SynchronizedDict，以及压入 reduce_queue 的流程

看上去很完美，运行也正确，没问题！


而 process_map 中，会进行 local_merge ，这部分的代码如下：
``` python
    def process_map(self):
        def worker():
            local_res = {}
            while not self.mapq.empty():
                k, v = self.mapq.get()
                for k2, v2 in self.map(k, v):
                    self.local_merge(local_res, k2, v2)
                self.mapq.task_done()
            for k, l in local_res.iteritems():
                v = self.local_reduce(k, l)
                self.mergeq.put(self.local_reduce(k, l))

        threads = []
        for i in range(self.workerNum):
            workerThread = threading.Thread(target=worker)
            workerThread.setDaemon(True)
            workerThread.start()
            threads.append(workerThread)
        self.mapq.join()
        # for th in threads:
        #     th.join()
```
看到，在 worker 中在处理完每个 queue 中的条目时，同样会调用 task_done，也就是使用 queue 来控制流程

于是，在 map_queue 空了的时候，主线程会从 mapq.join() 处继续运行，而其实就是结束 process_map 函数，继续调用 process_merge()

而，map_queue 空了的时候，worker 线程其实还未结束，因为最后还要做 local_reduce 的过程

什么意思？process_map 之 local_reduce 部分和 process_merge 函数会有重合运行的时机

假设，local_reduce 比较慢，而 process_merge 比较快，会导致 local_reduce 还没有把 reduce 的结果放到 merge_queue 中，process_merge 就已经处理完之前积攒的部分了

于是 merge_queue “暂时” 空掉，于是 process_merge 意外提前结束，导致整个流程发生错误

正确的做法，是要等 process_map 的 worker 都运行完毕了，才继续主线程的运行

也就是应该使用上面注释掉的部分代码，而不用 queue 来控制 process_map 的流程
