import json
from pathlib import Path

from kalman_experiments import Barrel, KalmanBarrelEstimator, LChanger, Logger
from simulator import Simulator


class KalmanInputController:
    def __init__(self, barrel: Barrel, l_estimator: KalmanBarrelEstimator, under_util: float):
        self.l_estimator = l_estimator
        self.period = l_estimator.period
        self.under_util = under_util
        self.barrel = barrel

    def do(self, t: float):
        l = self.l_estimator.l_estimation
        self.barrel.v = l * self.under_util


def run_kalman_control():
    output_file = Path('./logs/kalman_control_normal_limit.json')
    output_lines = []

    def l_fun(t: float) -> float:
        if 20 < t < 40:
            return 10
        else:
            return 7

    period = 1
    duration = period * 100
    under_util = 1

    barrel = Barrel(7, l_fun(0), v_dev=1, l_dev=1, d_dev=1, period=period)
    # barrel = Barrel(7, l_fun(0), -10, period)
    barrel_estimator = KalmanBarrelEstimator(barrel, period)
    l_changer = LChanger(barrel, l_fun)
    logger = Logger(barrel, barrel_estimator, output_lines)
    controller = KalmanInputController(barrel, barrel_estimator, under_util)
    simulator = Simulator([barrel, barrel_estimator, l_changer, controller, logger])
    simulator.simulate(duration)

    with open(output_file, mode='w') as file:
        for line in output_lines:
            file.write(f'{json.dumps(line)}\n')
    print('ready')


if __name__ == '__main__':
    run_kalman_control()
