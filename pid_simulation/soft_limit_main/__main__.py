import pandas as pd
import numpy as np
import re
import math
from processes import (
    S3,
    IntervalStorage,
    TaskExecutor,
    TasksLauncher,
    Logger,
    PID,
    SmartTasksLauncher,
    SoftResourceProvider,
    SoftResourceMaintainer,
    SoftResourceLogger
)
from simulator import Simulator

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

if __name__ == '__main__':
    res_provider = SoftResourceProvider(lambda t: 3 + math.sin(t))
    res_maintainer = SoftResourceMaintainer(res_provider, 0.01)

    exp_demander = ExponentialDemander(0.1, res_provider, 0.08)

    output_lines = []
    logger = SoftResourceLogger(0.01, res_provider, output_lines)

    processes = [res_maintainer, exp_demander, logger]
    simulator = Simulator(processes)
    simulator.simulate(10)

    # ====--------plotting--------------
    data = pd.DataFrame(output_lines)
    data.to_csv('soft_limit_control_log.csv')
