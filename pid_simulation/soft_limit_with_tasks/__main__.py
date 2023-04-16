from soft_limit_with_tasks.task_executors import (
    TaskExetutorQueueMaintainer,
    TaskExecutor,
    ResourceLogger
)
from task_model import Task
from soft_limit_with_tasks.resources import SoftResourceProvider
from soft_limit_with_tasks.launchers import (
    CheatingLauncher,
    PidLauncher,
    LauncherConfig,
    NaiveLauncher,
    ConstantRateLauncher,
    RelativeErrorPidLauncher
)
from soft_limit_with_tasks.target_demand_estimators import ExponentialEstimator
from simulator import Simulator

import pandas as pd
import math
import numpy as np


def test_on_stair_configurable(
    gen_task,
    stair_start: float,
    stair_end: float,
    stair_low: float,
    stair_high: float,
    estimator_margin: float,
    min_optimistic_shift: float,
    logged_points: float,
    queue_maintainer_period: float,
    simulated_duration: float,
    launcher,
    output_file: str,
):
    queue_maintainer_period = queue_maintainer_period

    def stair_fun(t: float) -> float:
        return stair_high if stair_start <= t < stair_end else stair_low

    res_provider = SoftResourceProvider(stair_fun)
    task_executor = TaskExecutor(res_provider)
    task_queue_maintainer = TaskExetutorQueueMaintainer(queue_maintainer_period, task_executor)
    demand_estimator = ExponentialEstimator(
        margin=estimator_margin,
        min_optimistic_shift=min_optimistic_shift,
        res_provider=res_provider,
        period=queue_maintainer_period
    )

    launcher_config = LauncherConfig(
        demand_estimator=demand_estimator,
        executor=task_executor,
        gen_task=gen_task,
        res_provider=res_provider,
        period=queue_maintainer_period
    )
    task_launcher = launcher(launcher_config)

    output_lines = []
    logger = ResourceLogger(period=simulated_duration / logged_points, executor=task_executor,
                            output_lines=output_lines)

    processes = [task_queue_maintainer, demand_estimator, task_launcher, logger]
    simulator = Simulator(processes)
    simulator.simulate(simulated_duration)

    # ====--------plotting--------------
    data = pd.DataFrame([line.__dict__ for line in output_lines])
    data.to_json(path_or_buf=output_file, orient='records', lines=True)


def test_on_stair(get_launcher, output_file: str):
    def gen_normal_task() -> Task:
        return Task(max(0.2, np.random.normal(1, 0)), max(0.2, np.random.normal(5000, 0)))

    test_on_stair_configurable(gen_task=gen_normal_task, stair_start=10_000.0, stair_end=20_000.0, stair_low=200.0,
                               stair_high=300.0, estimator_margin=0.1, min_optimistic_shift=1.5, logged_points=1000,
                               simulated_duration=30_000.0, queue_maintainer_period=5 * 60,
                               launcher=get_launcher, output_file=output_file)


def test_on_constant(get_launcher, output_file: str):
    def gen_normal_task() -> Task:
        return Task(max(0.2, np.random.normal(1, 0.0)), max(1, np.random.normal(500, 0)))

    test_on_stair_configurable(gen_task=gen_normal_task, stair_start=0.0, stair_end=5000.0 * 100, stair_low=2.0,
                               stair_high=2.0, estimator_margin=0.1, min_optimistic_shift=1.5, logged_points=1000,
                               simulated_duration=5000.0 * 2.2, queue_maintainer_period=5 * 60,
                               launcher=get_launcher, output_file=output_file)


def pid_launcher(config: LauncherConfig, k_p, k_i, k_d) -> PidLauncher:
    return PidLauncher(
        res_provider=config.res_provider,
        executor=config.executor,
        demand_estimator=config.demand_estimator,
        gen_task=config.gen_task,
        period=config.period,
        k_p=k_p, k_i=k_i, k_d=k_d
    )


def naive_launcher(config: LauncherConfig) -> NaiveLauncher:
    return NaiveLauncher(
        res_provider=config.res_provider,
        executor=config.executor,
        demand_estimator=config.demand_estimator,
        gen_task=config.gen_task,
        period=config.period,
    )


def cheating_launcher(config: LauncherConfig) -> CheatingLauncher:
    return CheatingLauncher(
        res_provider=config.res_provider,
        executor=config.executor,
        demand_estimator=config.demand_estimator,
        gen_task=config.gen_task,
        period=config.period,
    )


def constant_rate_launcher(config: LauncherConfig, slots: int) -> ConstantRateLauncher:
    return ConstantRateLauncher(
        res_provider=config.res_provider,
        executor=config.executor,
        slots=slots,
        gen_task=config.gen_task,
        period=config.period,
    )


def relative_pid_launcher(config: LauncherConfig, k_p, k_i, k_d) -> RelativeErrorPidLauncher:
    return RelativeErrorPidLauncher(
        res_provider=config.res_provider,
        executor=config.executor,
        demand_estimator=config.demand_estimator,
        gen_task=config.gen_task,
        period=config.period,
        k_p=k_p, k_i=k_i, k_d=k_d
    )


if __name__ == '__main__':
    # def gen_task() -> Task:
    #     return Task(1, 1)
    #
    # def gen_normal_task() -> Task:
    #     return Task(max(0.2, np.random.normal(2, 0.5)), max(0.2, np.random.normal(1, 0.5)))
    #
    # res_provider = SoftResourceProvider(lambda t: 100 + 10 * math.sin(t / 1.5))
    # task_executor = TaskExecutor(res_provider)
    # task_queue_maintainer = TaskExetutorQueueMaintainer(0.01, task_executor)
    # demand_estimator = ExponentialEstimator(
    #     margin=0.05,
    #     min_optimistic_shift=2,
    #     res_provider=res_provider,
    #     period=0.01
    # )
    # # task_launcher = ExponentialLauncher(0.1, res_provider, task_executor, gen_task, 0.01)
    # task_launcher = CheatingLauncher(res_provider, task_executor, gen_normal_task, demand_estimator, 0.01)
    # # task_launcher = PidLauncher(res_provider, task_executor, gen_normal_task, demand_estimator,
    # #                             k_p=62, k_i=0.0, k_d=0.0,
    # #                             period=0.01)
    #
    # output_lines = []
    # logger = ResourceLogger(period=0.01, executor=task_executor, output_lines=output_lines)
    #
    # processes = [task_queue_maintainer, demand_estimator, task_launcher, logger]
    # simulator = Simulator(processes)
    # simulator.simulate(20)
    #
    # # ====--------plotting--------------
    # data = pd.DataFrame([line.__dict__ for line in output_lines])
    # data.to_json('soft_limit_with_tasks_exponential_control_log.json')

    # test_on_stair(lambda config: pid_launcher(config, k_p=1.5, k_i=0.003, k_d=0), 'pid_stair.json')
    # test_on_stair(lambda config: pid_launcher(config, k_p=0.005, k_i=0.00001, k_d=0), 'pid_stair.json')
    # test_pid_on_stair(k_p=14, k_i=0.0, k_d=0.0)
    # test_on_constant(lambda config: pid_launcher(config, k_p=0.003, k_i=0.00001, k_d=1.3), 'constant_pid.json')

    # ----------------- another launcher -----------------

    # test_on_stair(naive_launcher, 'soft_limit_naive.json')

    # ----------------- another launcher -----------------

    # test_on_stair(cheating_launcher, 'soft_limit_cheating.json')
    # test_on_constant(cheating_launcher, 'constant_cheating.json')

    # ----------------- constant launcher -----------------

    # test_on_constant(lambda config: constant_rate_launcher(config, 2), 'constant_constant.json')

    # ----------------- relative error pid launcher -----------------

    test_on_stair(lambda config: relative_pid_launcher(config, k_p=0.5, k_i=0.0001, k_d=0), 'logs/pid_stair.json')
