from soft_limit_with_tasks.resources import SoftResourceProvider
from soft_limit_with_tasks.task_executors import TaskExecutor


class ExponentialEstimator:
    def __init__(
        self,
        margin,
        min_optimistic_shift: float,
        res_provider: SoftResourceProvider,
        period: float
    ):
        self.margin = margin
        self.min_optimistic_shift = min_optimistic_shift
        self.res_provider = res_provider
        self.period = period
        self.target_demand = self._calculate_target_demand(self.res_provider.usage)

    def _calculate_target_demand(self, usage) -> float:
        return max(usage + self.min_optimistic_shift, usage * (1 + self.margin))

    def do(self, t):
        usage = self.res_provider.usage
        self.target_demand = self._calculate_target_demand(usage)

    def get_target_demand(self, t) -> float:
        return self.target_demand
