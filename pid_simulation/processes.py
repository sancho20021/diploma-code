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


# Раз в period квантов времени замеряет показатели s3 usage, demand, interval
class Logger:
    def __init__(self, period: float, interval: IntervalStorage, s3: S3, task_executor: TaskExecutor, output_lines):
        self.period = period
        self.interval = interval
        self.s3 = s3
        self.task_executor = task_executor
        self.output_lines = output_lines

    def do(self, t):
        self.task_executor.clear_finished(t)
        message = {
            'interval': self.interval.get(),
            's3_usage': self.s3.get_usage(),
            's3_limit': self.s3.get_capacity()
        }
        self.output_lines.append(message)
        print(message)


# each period time,
# observes the s3 usage, limit and
# offers new interval into interval
class PID:
    def __init__(self,
                 s3: S3,
                 interval: IntervalStorage,
                 period: float,
                 Kp: float,
                 Ki: float,
                 Kd: float,
                 init_interval: float):
        self.name = "PID"
        self.s3 = s3
        self.interval = interval
        self.period = period
        self.init_interval = init_interval  ## seconds

        self.e_prev = 0
        self.t_prev = None  # seconds
        self.observed_prev = s3.get_usage()
        self.I = 0

        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

    def do(self, t):
        now = t
        self.t_prev = self.t_prev or now - self.period

        desired = self.s3.get_capacity()
        observed = self.s3.get_usage()

        error = desired - observed
        time_passed = now - self.t_prev
        P = self.Kp * error
        self.I = self.I + self.Ki * error * time_passed
        D = self.Kd * (observed - self.observed_prev) / time_passed

        # TODO: extract minimal interval to parameter
        U = max(0.01, P + self.I + D)  # seconds
        self.interval.set(U)

        # print(f'dt = {time_passed}, '
        #       f'desired = {desired}, '
        #       f'observed = {observed}, '
        #       f'init_interval + K*P = {self.init_interval + P}')

        self.e_prev = error
        self.t_prev = now
        self.observed_prev = observed


class SmartTasksLauncher:
    def __init__(self, s3: S3, task_executor: TaskExecutor, period: float):
        self.s3 = s3
        self.task_executor = task_executor
        self.period = period

    def do(self, t: float):
        task = Task(size=np.random.normal(4, 1), duration=np.random.normal(4, 2))
        if self.s3.get_usage() + task.size <= self.s3.get_capacity():
            self.task_executor.execute(t, task)


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


class ExponentialDemander:
    def __init__(self, margin, res_provider: SoftResourceProvider, period: float):
        self.margin = margin
        self.res_provider = res_provider
        self.period = period

    def do(self, t):
        usage = self.res_provider.usage
        demand = self.res_provider.demand
        assert usage <= demand
        new_demand = max(0.01, usage * (1 + self.margin))
        self.res_provider.require(t, new_demand)


class SoftResourceLogger:
    def __init__(self, period: float, res_provider: SoftResourceProvider, output_lines):
        self.period = period
        self.res_provider = res_provider
        self.output_lines = output_lines

    def do(self, t):
        message = {
            'usage': self.res_provider.usage,
            'demand': self.res_provider.demand,
            'actual_limit': self.res_provider.capacity_fun(t)
        }
        self.output_lines.append(message)
        print(message)
