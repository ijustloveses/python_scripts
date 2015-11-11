# encoding: utf-8

from Queue import Queue


class Task(object):
    """
        A task is a wrapper around a coroutine
        run() executes the task to the next yield (a trap)
    """
    taskid = 0

    def __init__(self, target):
        Task.taskid += 1
        self.tid = Task.taskid
        self.target = target    # target coroutine
        self.sendval = None

    def run(self):
        """ task runs until it hits the yield """
        return self.target.send(self.sendval)


class SystemCall(object):
    """
        Base class of SystemCall
        A system call is to request the service of the scheduler,
        tasks will use the yield statement with a value
    """
    def handle(self):
        pass


class GetTid(SystemCall):
    """
        A example of system call
    """
    def handle(self):
        self.task.sendval = self.task.tid    # so tid will be sent by Task.run()
        self.sched.schedule(self.task)


class NewTask(SystemCall):
    """
        新建 Task 系统任务，传入任务 target coroutine
        然后将新建一个 task，连同自身 task 一起再次 schedule
    """
    def __init__(self, target):
        self.target = target

    def handle(self):
        tid = self.sched.new(self.target)    # schedule target instead of task itself
        self.task.sendval = tid              # target's tid, diff from task's tid
        self.sched.schedule(self.task)       # schedule task too, in case task is not finish


class KillTask(SystemCall):
    def __init__(self, tid):
        self.tid = tid

    def handle(self):
        task = self.sched.taskmap.get(self.tid, None)
        if task:
            task.target.close()    # close coroutine
            self.task.sendval = True
        else:
            self.task.sendval = False
        self.sched.schedule(self.task)


class WaitTask(SystemCall):
    def __init__(self, tid):
        self.tid = tid

    def handle(self):
        result = self.sched.waitforexit(self.task, self.tid)
        self.task.sendval = result
        if not result:
            self.sched.schedule(self.task)


class Scheduler(object):
    """
        Scheduler maintains a queue of tasks that ready to run,
        and a dictionary that keeps track of all active tasks
    """
    def __init__(self):
        self.ready = Queue()
        self.taskmap = {}
        self.exit_waiting = {}   # for task waiting feature

    def new(self, target):
        newtask = Task(target)
        self.taskmap[newtask.tid] = newtask
        self.schedule(newtask)
        return newtask.tid

    def schedule(self, task):
        self.ready.put(task)

    def exit(self, task):
        print "Task %d terminated" % task.tid
        del self.taskmap[task.tid]
        # 对于 waiting 的任务，当子任务结束，恢复 schedule
        for task in self.exit_waiting.pop(task.tid, []):
            self.schedule(task)

    def waitforexit(self, task, waittid):
        if waittid in self.taskmap:
            self.exit_waiting.setdefault(waittid, []).append(task)
            return True
        else:
            return False

    def mainloop(self):
        """
            pulls tasks off the queue and runs them to the next yield,
            then the scheduler regains control and switches to the other task
        """
        while self.taskmap:
            task = self.ready.get()
            try:
                result = task.run()
                """
                    If the result yielded by the task is a SystemCall,
                    do some setup and run it "on behalf of the task"
                """
                if isinstance(result, SystemCall):
                    result.task = task
                    result.sched = self
                    result.handle()    # run it
                    continue
            except StopIteration:
                """ remove task on exception """
                self.exit(task)
                continue
            self.schedule(task)


if __name__ == '__main__':
    def foo():
        mytid = yield GetTid()
        print 'mytid', mytid
        for i in xrange(5):
            print "Foo: ", mytid
            yield

    def bar():
        mytid = yield GetTid()
        while True:
            print "Bar: ", mytid
            yield

    def sometask():
        tid = yield NewTask(bar())
        print "New task: %d" % tid
        for i in xrange(10):
            yield
        yield KillTask(tid)
        print "Done"

    def waittask():
        child = yield NewTask(foo())
        print "waiting for child"
        yield WaitTask(child)
        print "Child done"

    sched = Scheduler()
    sched.new(waittask())
    sched.new(sometask())
    sched.mainloop()
