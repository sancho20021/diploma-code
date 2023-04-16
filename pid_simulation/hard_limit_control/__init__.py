from task_model import (
    S3, IntervalStorage,
    Task, TaskExecutor
)

import numpy as np


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
