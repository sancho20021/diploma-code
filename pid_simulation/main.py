# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import pandas as pd
import numpy as np
import re
import math
from task_model import (
    S3,
    IntervalStorage,
    TaskExecutor,
    TasksLauncher,
)

from hard_limit_control import (
    PID,
    SmartTasksLauncher
)

from task_model.loggers import Logger

from simulator import Simulator


class S3Modifier:
    def __init__(self, default_cap: float, intervals_with_other_cap, period: float, s3: S3):
        self.default_cap = default_cap
        self.intervals_with_other_cap = intervals_with_other_cap
        self.period = period
        self.s3 = s3

    def do(self, t: float):
        for l, r, value in self.intervals_with_other_cap:
            if l <= t < r:
                self.s3.cap = value
            else:
                self.s3.cap = self.default_cap


if __name__ == '__main__':
    pid_period = 0.2
    cleanup_period = 0.02
    logger_period = 0.03
    s3_capacity = 100
    init_interval = 4 / s3_capacity
    Kp = -0.00005
    Ki = -0.001
    Kd = 0.000

    s3 = S3(s3_capacity)
    interval = IntervalStorage(init_interval)
    task_executor = TaskExecutor(s3)
    output_lines = []

    task_launcher = TasksLauncher(
        interval=interval,
        task_executor=task_executor,
        cleanup_period=cleanup_period
    )
    logger = Logger(
        logger_period, interval=interval, s3=s3, output_lines=output_lines, task_executor=task_executor
    )

    # interval_controller = asyncio.create_task(ConstantIntervalController(interval=interval).run())
    interval_controller = PID(
        s3=s3,
        interval=interval,
        period=pid_period,
        Kp=Kp, Ki=Ki, Kd=Kd,
        init_interval=init_interval
    )

    s3_modifier = S3Modifier(
        default_cap=s3_capacity,
        intervals_with_other_cap=[(100, 200, 20)],
        period=1,
        s3=s3
    )

    # ----------- PID
    # processes = [task_launcher, logger, interval_controller, s3_modifier]

    # ------ Smart Estimator
    processes = [SmartTasksLauncher(s3=s3, task_executor=task_executor, period=0.01), logger, s3_modifier]

    simulator = Simulator(processes)
    simulator.simulate(400)

    # ====--------plotting--------------
    data = pd.DataFrame(output_lines)
    data.to_csv('pid_interval_control_log.csv')
