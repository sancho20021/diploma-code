import json
from pathlib import Path

from kalman_experiments import Barrel, LChanger
from kalman_experiments.p_fluid_control import Logger
from simulator import Simulator


class AnalyticalInputController:
    def __init__(self, barrel: Barrel):
        self.period = barrel.period
        self.barrel = barrel
        self.d_prev = barrel.d

    def do(self, t: float):
        self.barrel.v = self.barrel.v + (self.d_prev - self.barrel.d) / self.period


def run_analytical_control():
    output_file = Path('./logs/analytical_control_normal.json')
    output_lines = []

    def l_fun(t: float) -> float:
        if 20 < t < 40:
            return 10
        else:
            return 5

    period = 1
    duration = period * 100
    under_util = 1.

    barrel = Barrel(7, l_fun(0), l_dev=1, v_dev=1, d_dev=1, period=period)
    l_changer = LChanger(barrel, l_fun)
    logger = Logger(barrel, output_lines)
    controller = AnalyticalInputController(barrel)
    simulator = Simulator([barrel, l_changer, controller, logger])
    simulator.simulate(duration)

    with open(output_file, mode='w') as file:
        for line in output_lines:
            file.write(f'{json.dumps(line)}\n')
    print('ready')


if __name__ == '__main__':
    run_analytical_control()