import dataclasses
import math
from typing import Any

from soft_limit_with_tasks.resources import SoftResourceProvider
from soft_limit_with_tasks.task_executors import TaskExecutor
from soft_limit_with_tasks.target_demand_estimators import ExponentialEstimator


@dataclasses.dataclass
class LauncherConfig:
    res_provider: SoftResourceProvider
    executor: TaskExecutor
    gen_task: Any
    demand_estimator: Any
    period: float


class CheatingLauncher:
    def __init__(
        self,
        res_provider: SoftResourceProvider,
        executor: TaskExecutor,
        gen_task,
        demand_estimator: ExponentialEstimator,
        period: float
    ):
        self.res_provider = res_provider
        self.executor = executor
        self.gen_task = gen_task
        self.demand_estimator = demand_estimator
        self.period = period

    def do(self, t):
        demand = self.executor.get_demand(t)

        new_demand = self.demand_estimator.get_target_demand(t)
        available_space = new_demand - demand

        while available_space > 0:
            task = self.gen_task()
            assert task.size > 0
            if task.size > available_space:
                break
            self.executor.launch(task, t)
            available_space -= task.size


class PidLauncher:
    """
    Его запускают строго раз в period секунд
    """

    def __init__(
        self,
        res_provider: SoftResourceProvider,
        executor: TaskExecutor,
        gen_task,
        demand_estimator: ExponentialEstimator,
        k_p: float,
        k_i: float,
        k_d: float,
        period: float
    ):
        self.res_provider = res_provider
        self.executor = executor
        self.gen_task = gen_task
        self.demand_estimator = demand_estimator
        self.period = period

        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d

        self.e_prev = 0
        self.sum_e_prev = 0

    def _pid(self, e: float) -> float:
        return self.k_p * e \
            + self.k_d / self.period * (e - self.e_prev) \
            + self.k_i * self.period * (self.sum_e_prev + e)

    def do(self, t):
        demand = self.executor.get_demand(t)
        target_demand = self.demand_estimator.get_target_demand(t)

        e = target_demand - demand
        u = self._pid(e)
        print(f'error={e}, u={u}')

        if self.e_prev < 0 < e or self.e_prev > 0 > e:
            self.sum_e_prev = 0
            print('error crossed zero, setting sum to 0')

        self.e_prev = e
        self.sum_e_prev += e

        slots = math.floor(max(0.0, self.period * u))
        # slots = math.floor(max(0.0, u))
        print(f'slots={slots}')
        assert slots < 1000
        for i in range(slots):
            task = self.gen_task()
            self.executor.launch(task, t)


class RelativeErrorPidLauncher:
    """
    Его запускают строго раз в period секунд
    """

    def __init__(
        self,
        res_provider: SoftResourceProvider,
        executor: TaskExecutor,
        gen_task,
        demand_estimator: ExponentialEstimator,
        k_p: float,
        k_i: float,
        k_d: float,
        period: float
    ):
        self.res_provider = res_provider
        self.executor = executor
        self.gen_task = gen_task
        self.demand_estimator = demand_estimator
        self.period = period

        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d

        self.e_prev = 0
        self.sum_e_prev = 0

    def _pid(self, e: float) -> float:
        return self.k_p * e \
            + self.k_d / self.period * (e - self.e_prev) \
            + self.k_i * self.period * (self.sum_e_prev + e)

    def do(self, t):
        demand = self.executor.get_demand(t)
        target_demand = self.demand_estimator.get_target_demand(t)

        e = (target_demand - demand) / target_demand
        u = self._pid(e)
        print(f'error={e}, u={u}')

        if self.e_prev < 0 < e or self.e_prev > 0 > e:
            self.sum_e_prev = 0
            print('error crossed zero, setting sum to 0')

        self.e_prev = e
        self.sum_e_prev += e

        slots = math.floor(max(0.0, self.period * u))
        # slots = math.floor(max(0.0, u))
        print(f'slots={slots}')
        assert slots < 1000
        for i in range(slots):
            task = self.gen_task()
            self.executor.launch(task, t)


class NaiveLauncher:
    def __init__(
        self,
        res_provider: SoftResourceProvider,
        executor: TaskExecutor,
        gen_task,
        demand_estimator: ExponentialEstimator,
        period: float
    ):
        self.res_provider = res_provider
        self.executor = executor
        self.gen_task = gen_task
        self.demand_estimator = demand_estimator
        self.period = period

        self.e_prev = 0
        self.sum_e_prev = 0

    def do(self, t):
        demand = self.executor.get_demand(t)
        target_demand = self.demand_estimator.get_target_demand(t)

        if demand < target_demand:
            for i in range(32):
                self.executor.launch(self.gen_task(), t)


class ConstantRateLauncher:
    def __init__(
        self,
        res_provider: SoftResourceProvider,
        executor: TaskExecutor,
        gen_task,
        slots: int,
        period: float
    ):
        self.res_provider = res_provider
        self.executor = executor
        self.gen_task = gen_task
        self.slots = slots
        self.period = period

        self.e_prev = 0
        self.sum_e_prev = 0

    def do(self, t):
        for i in range(self.slots):
            self.executor.launch(self.gen_task(), t)
