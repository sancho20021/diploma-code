from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True, eq=True)
class Task:
    size: float
    duration: float


@dataclass(frozen=True, eq=True)
class TaskInstance:
    started: float
    task: Task


class S3:
    def __init__(self, cap: int):
        self.cap = cap
        self.usage = 0

    def alloc(self, s: int):
        self.usage += s

    def free(self, s: int):
        self.usage = max(0, self.usage - s)

    def get_usage(self) -> int:
        return self.usage

    def get_capacity(self) -> int:
        return self.cap


class TaskExecutor:
    def __init__(self, s3: S3):
        self.s3 = s3
        self.tasks_running = []

    def execute(self, t: float, task: Task):
        self.clear_finished(t)
        when = t
        instance = TaskInstance(started=when, task=task)
        self.tasks_running.append(instance)
        self.s3.alloc(task.size)

    def clear_finished(self, t: float):
        now = t
        expired = [t for t in self.tasks_running if t.started + t.task.duration < now]
        expired_set = set(expired)
        self.tasks_running[:] = [t for t in self.tasks_running if t not in expired_set]
        for t in expired:
            self.s3.free(t.task.size)

    def get_running(self, t: float):
        self.clear_finished(t)
        return self.tasks_running

# shared контейнер для хранения текущего интервала
class IntervalStorage:
    def __init__(self, interval: float):
        self.interval = interval

    def set(self, interval: float):
        self.interval = interval

    def get(self) -> float:
        return self.interval


# TODO: заменить константы на параметры
class TasksLauncher:
    def __init__(self, interval: IntervalStorage, task_executor: TaskExecutor, cleanup_period: float):
        self.interval = interval
        self.task_executor = task_executor
        self.period = interval.get()

    def do(self, t: float):
        self.task_executor.execute(t, Task(size=np.random.normal(4, 1), duration=np.random.normal(4, 2)))
        self.period = self.interval.get()


class SoftResourceProvider:
    def __init__(self, capacity_fun):
        self.capacity_fun = capacity_fun
        self.demand = 0
        self.usage = 0

    def require(self, t, x):
        self.demand = x
        self.usage = min(self.capacity_fun(t), x)

    def update_usage(self, t):
        self.usage = min(self.capacity_fun(t), self.usage)


class SoftResourceMaintainer:
    def __init__(self, res_provider: SoftResourceProvider, period: float):
        self.res_provider = res_provider
        self.period = period

    def do(self, t):
        self.res_provider.update_usage(t)