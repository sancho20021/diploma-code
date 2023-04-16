import dataclasses
from collections import deque
from processes import Task, TaskInstance
from soft_limit_with_tasks.resources import SoftResourceProvider
import json


# executor of tasks that immediately allocates resources after starting
class TaskExecutor:
    def __init__(self, res_provider: SoftResourceProvider):
        self.res_provider = res_provider
        self.pending = deque()
        self.paused = deque()
        self.running = []

    def launch(self, task: Task, t: float):
        self.pending.append(task)
        # print('new pending task')
        self.clear_finished(t)
        self.try_launch_paused(t)
        if len(self.paused) == 0:
            self.try_launch_pending(t)

    def clear_finished(self, t: float):
        now = t
        expired = [task for task in self.running if task.started + task.task.duration < now]
        # print(f'found expired tasks: {expired}')
        expired_set = set(expired)
        # print(f'running before clearing: {self.running}')
        self.running[:] = [t for t in self.running if t not in expired_set]
        # print(f'running after clearing: {self.running}')
        for t in expired:
            self.res_provider.free(t, t.task.size)
        # print(f'usage after clearing: {self.res_provider.usage}')

    def try_launch(self, t: float, task: Task) -> bool:
        if self.res_provider.try_alloc(t, task.size):
            self.running.append(TaskInstance(t, task))
            return True
        else:
            return False

    def pause_if_necessary(self, t: float):
        while self.res_provider.limit_exceeded(t):
            assert len(self.running) > 0
            paused_instance = self.running.pop(0)
            left_dur = paused_instance.task.duration - (t - paused_instance.started)
            assert t >= paused_instance.started
            assert left_dur > 0
            self.paused.append(Task(paused_instance.task.size, left_dur))
            self.res_provider.free(t, paused_instance.task.size)

    def try_launch_paused(self, t: float):
        while len(self.paused) > 0:
            if self.try_launch(t, self.paused[0]):
                self.paused.popleft()
            else:
                return

    def try_launch_pending(self, t: float):
        while len(self.pending) > 0:
            if self.pending:
                if self.try_launch(t, self.pending[0]):
                    self.pending.popleft()
                else:
                    return

    def get_demand(self, t: float):
        self.clear_finished(t)

        sum = 0
        for task in self.pending + self.paused:
            sum += task.size
        for task in self.running:
            sum += task.task.size
        return sum


class TaskExetutorQueueMaintainer:
    def __init__(self, period: float, task_executor: TaskExecutor):
        self.period = period
        self.task_executor = task_executor

    def do(self, t: float):
        self.task_executor.clear_finished(t)
        self.task_executor.pause_if_necessary(t)
        self.task_executor.try_launch_paused(t)
        if len(self.task_executor.paused) == 0:
            self.task_executor.try_launch_pending(t)


class ResourceLogger:
    def __init__(self, period: float, executor: TaskExecutor, output_lines):
        self.period = period
        self.executor = executor
        self.output_lines = output_lines

    def do(self, t):
        record = UtilizationRecord(
            usage=self.executor.res_provider.usage,
            demand=self.executor.get_demand(t),
            actual_limit=self.executor.res_provider.capacity_fun(t),
            time=t
        )
        self.output_lines.append(record)
        print(record)


@dataclasses.dataclass
class UtilizationRecord:
    usage: float
    demand: float
    actual_limit: float
    time: float

    @property
    def __dict__(self):
        return dataclasses.asdict(self)

    @property
    def json(self):
        return json.dumps(self.__dict__)
