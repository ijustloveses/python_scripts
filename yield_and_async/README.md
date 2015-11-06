Examples of Python asynchronous manipulations with yield and coroutine

References:
-------------
http://sahandsaba.com/combinatorial-generation-using-coroutines-in-python.html
https://github.com/sahands/coroutine-generation
http://xidui.github.io/2015/10/29/%E6%B7%B1%E5%85%A5%E7%90%86%E8%A7%A3python3-4-Asyncio%E5%BA%93%E4%B8%8ENode-js%E7%9A%84%E5%BC%82%E6%AD%A5IO%E6%9C%BA%E5%88%B6/

One simple yield example:
--------------------------
>>> def fib():
...     a, b = 0, 1
...     while True:
...             y = yield b
...             print y
...             a, b = b, a+b
...
>>> f = fib()
>>> next(f)
1
>>> print next(f)
None
1
>>> print next(f)
None
2
>>> next(f)
None
3
>>> f.send('aa')
aa      <--- y will be the value sent to the generator --->
5
>>> print f.send('bb')
bb
8

Workflow tracking in 03 event loop
------------------------------------
Take hello_task as example:
1. hello_task = print_eveny('Hello', 1), so hello_task is a generator which yield sleep_for_seconds object
2. loop.schedule(hello_task), make a partial of resume_task func, and append to loop._tasks
3. loop.run_forever, take task from loop._tasks, and run task(), which will call resume_task(hello_task)
4. resume_task(hello_task), send None to hello_task generator and get a sleep_for_seconds obj, so schedule hello_task again
5. schedule with when=sleep_for_seconds._wait_time, so this time hello_task coroutine is wrapped by resume_task and  insorted into loop._timers
6. loop.run_forever, take task from loop._timers, and run again, which will call resume_task(hello_task) again, and schedule hello_task again
7. .....

from the workflow, we can find the key points:
- coroutines are all implemented as generators
- during schedule, couroutine are wrapped into resume_task partial
- during running, coroutine generator is triggered by resume_task, and the latter will schedule coroutine again via the result
- so, the workflow runs like:
    loop schedule coroutine, which is wrapped into a partial of resume_task func
        loop take task, and run the resume_task with the coroutine as the 1st parameter
            -> resume_task trigger coroutine by sending value to coroutine
               -> coroutine run an iteration and return result to resume_task
                    -> resume_task checks the result and schedule the coroutine again


