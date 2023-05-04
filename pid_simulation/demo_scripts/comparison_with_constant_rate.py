from soft_limit_with_tasks.task_executors import (
    TaskExetutorQueueMaintainer,
    TaskExecutor,
    ResourceLogger
)
from task_model import Task
from soft_limit_with_tasks.resources import SoftResourceProvider
from soft_limit_with_tasks.launchers import (
    ConstantRateLauncher,
    ProportionalLauncher,
    RelativePidLauncher2, KalmanLauncher
)
from soft_limit_with_tasks.target_demand_estimators import ExponentialEstimator
from simulator import Simulator

import pandas as pd
import dataclasses
import numpy as np
from typing import Callable, Any


@dataclasses.dataclass
class LauncherConfig2:
    res_provider: SoftResourceProvider
    executor: TaskExecutor
    gen_task: Callable[[], Task]
    period: float


def test_on_constant_configurable(
        launcher_period: float,
        capacity: float,
        logged_points: float,
        queue_maintainer_period: float,
        simulated_duration: float,
        launcher: Callable[[LauncherConfig2], Any],
        gen_task: Callable[[], Task],
        output_file: str,
):
    res_provider = SoftResourceProvider(lambda t: capacity)
    task_executor = TaskExecutor(res_provider)
    task_queue_maintainer = TaskExetutorQueueMaintainer(queue_maintainer_period, task_executor)

    launcher_config = LauncherConfig2(res_provider, task_executor, gen_task, launcher_period)

    task_launcher = launcher(launcher_config)
    output_lines = []
    logger = ResourceLogger(period=simulated_duration / logged_points, executor=task_executor,
                            output_lines=output_lines)

    processes = [task_queue_maintainer, task_launcher, logger]
    simulator = Simulator(processes)
    simulator.simulate(simulated_duration)

    # ====--------plotting--------------
    data = pd.DataFrame([line.__dict__ for line in output_lines])
    data.to_json(path_or_buf=output_file, orient='records', lines=True)


def constant_rate_launcher(config: LauncherConfig2, slots: int) -> ConstantRateLauncher:
    return ConstantRateLauncher(
        res_provider=config.res_provider,
        executor=config.executor,
        slots=slots,
        gen_task=config.gen_task,
        period=config.period,
    )


def proportional_launcher(config: LauncherConfig2, step, optimistic_delta) -> ProportionalLauncher:
    return ProportionalLauncher(
        executor=config.executor,
        step=step,
        optimistic_delta=optimistic_delta,
        gen_task=config.gen_task,
        period=config.period,
    )


def pid_launcher(config: LauncherConfig2, step: float, optimistic_delta: float, k_i: float, k_d: float) -> RelativePidLauncher2:
    return RelativePidLauncher2(
        executor=config.executor,
        gen_task=config.gen_task,
        optimistic_delta=optimistic_delta,
        step=step,
        k_i=k_i,
        k_d=k_d,
        period=config.period
    )


if __name__ == '__main__':
    task_size = 1
    task_size_dev = 0.5
    task_duration = 10
    task_duration_dev = 1
    step = 5
    optimistic_delta = 0.05

    def gen_task() -> Task:
        ts = max(0.1, np.random.normal(task_size, task_size_dev))
        td = max(0.1, np.random.normal(task_duration, task_duration_dev))
        return Task(ts, td)


    def p_launcher(config: LauncherConfig2) -> ProportionalLauncher:
        return proportional_launcher(config, step=step, optimistic_delta=optimistic_delta)

    def const_launcher(config: LauncherConfig2) -> ConstantRateLauncher:
        constant_slots = 1
        return constant_rate_launcher(config, constant_slots)

    def pid_launcher_fixed(config: LauncherConfig2) -> RelativePidLauncher2:
        step_pid = 3
        k_i = 0
        k_d = 0
        return pid_launcher(config, step_pid, optimistic_delta, k_i=k_i, k_d=k_d)

    def kalman_launcher(config: LauncherConfig2) -> KalmanLauncher:
        s_mean = task_duration
        s_dev = task_duration_dev
        l_dev = 1
        v_underutil = 0.95
        return KalmanLauncher(
            executor=config.executor,
            gen_task=config.gen_task,
            s_mean=s_mean,
            s_dev=s_dev,
            l_dev=l_dev,
            v_underutil=v_underutil,
            period=config.period
        )


    # test_on_constant_configurable(launcher_period=0.1,
    #                               capacity=300, logged_points=1000,
    #                               simulated_duration=100, queue_maintainer_period=0.1,
    #                               gen_task=gen_task,
    #                               launcher=p_launcher, output_file='logs/comparison/p_5.json')

    # test_on_constant_configurable(launcher_period=1,
    #                               capacity=11, logged_points=1000,
    #                               simulated_duration=200, queue_maintainer_period=0.4,
    #                               gen_task=gen_task,
    #                               launcher=const_launcher, output_file='logs/comparison/constant1.json')

    # test_on_constant_configurable(launcher_period=1,
    #                               capacity=11, logged_points=1000,
    #                               simulated_duration=200, queue_maintainer_period=0.4,
    #                               gen_task=gen_task,
    #                               launcher=pid_launcher_fixed, output_file='logs/comparison/pid1.json')

    test_on_constant_configurable(launcher_period=1,
                                  capacity=11, logged_points=1000,
                                  simulated_duration=200, queue_maintainer_period=0.4,
                                  gen_task=gen_task,
                                  launcher=kalman_launcher, output_file='logs/comparison/kalman.json')
