import json
from pathlib import Path

import numpy as np
from filterpy.kalman import KalmanFilter
from typing import Callable

from simulator import Simulator


class Barrel:
    def __init__(self, v0: float, l0: float, d_dev: float, l_dev: float, v_dev: float, period: float):
        self.v = v0
        self.l = l0
        self.d = 0
        self.v_dev = v_dev
        self.l_dev = l_dev
        self.d_dev = d_dev
        # self.min_demand = min_demand
        self.period = period

    def do(self, t: float):
        v = np.random.normal(self.v, self.v_dev)
        l = np.random.normal(self.l, self.l_dev)
        self.d = self.d + (v - l) * self.period + np.random.normal(0, self.d_dev)
        # self.d = max(0., self.d + (self.v - self.l) * self.period)
        # self.d = max(self.min_demand, self.d + (self.v - self.l) * self.period)


class KalmanBarrelEstimator:
    def __init__(self, barrel: Barrel, period: float):
        self.period = period
        self.barrel = barrel
        self.f = KalmanFilter(dim_x=3, dim_z=2)
        self.f.x = np.array([1., barrel.v, 0.])
        self.f.H = np.array([[0., 1., 0.],
                             [0., 0., 1.]])
        self.f.P *= 100
        self.f.R = np.array([[0., 0.],
                             [0., 0.]])
        self.f.Q = np.array([[1., 0., 0.],
                             [0., 1., 0.],
                             [0., 0., 1.]])
        self.l_estimation = self.f.x[0]

    def do(self, t: float):
        self.f.F = np.array([[1., 0., 0.],
                             [0., 1., 0.],
                             [-self.period, self.period, 1.]])

        v = self.barrel.v
        d = self.barrel.d
        z = np.array([v, d])
        self.f.predict()
        self.f.update(z)
        self.l_estimation = self.f.x[0]
        print(f'{self.f.x=}')
        print(f'{self.f.P=}')


class LChanger:
    def __init__(self, barrel: Barrel, l_fun: Callable[[float], float]):
        self.barrel = barrel
        self.l_fun = l_fun
        self.period = barrel.period

    def do(self, t: float):
        self.barrel.l = self.l_fun(t)


class Logger:
    def __init__(self, barrel: Barrel, barrel_estimator: KalmanBarrelEstimator, output_lines: list[dict]):
        self.barrel = barrel
        self.barrel_estimator = barrel_estimator
        self.period = barrel_estimator.period
        self.output_lines = output_lines

    def do(self, t: float):
        d = self.barrel.d
        v = self.barrel.v
        real_l = self.barrel.l
        estimated_l = self.barrel_estimator.l_estimation
        data = {'d': d, 'v': v, 'l_actual': real_l, 'l_estimated': estimated_l, 't': t}
        print(f'{t=}, {data=}')
        self.output_lines.append(data)


def run_kalman_experiment():
    output_file = Path('./logs/kalman_normal_no_control.json')
    output_lines = []

    def l_fun(t: float) -> float:
        if 20 < t < 40:
            return 10
        else:
            return 5

    period = 1
    duration = period * 70

    barrel = Barrel(7, l_fun(0), v_dev=1, l_dev=1, d_dev=1, period=period)
    barrel_estimator = KalmanBarrelEstimator(barrel, period)
    l_changer = LChanger(barrel, l_fun)
    logger = Logger(barrel, barrel_estimator, output_lines)
    simulator = Simulator([barrel, barrel_estimator, l_changer, logger])
    simulator.simulate(duration)

    with open(output_file, mode='w') as file:
        for line in output_lines:
            file.write(f'{json.dumps(line)}\n')
    print('ready')


if __name__ == '__main__':
    # f = KalmanFilter(dim_x=3, dim_z=2)
    # f.x = np.array([1., 1., 0.])
    # # f.F = np.array([[]])
    # f.H = np.array([[0., 1., 0.],
    #                 [0., 0., 1.]])
    # f.P *= 100
    # f.R = np.array([[0., 0.],
    #                 [0., 0.]])
    # s_dev = 1
    # l_dev = 1
    # f.Q = np.array([[l_dev ** 2, 0., 0.],
    #                 [0., 0., 0.],
    #                 [0., 0., s_dev ** 2]])
    #
    # t = 0
    # s = 2
    # dt = 1
    # for _ in range(10):
    #     f.F = np.array([[1., 0., 0.],
    #                     [0., 1., 0.],
    #                     [-dt, s * dt, 1.]])
    #
    #     v, d = map(float, input().split())
    #     z = np.array([v, d])
    #     f.predict()
    #     f.update(z)
    #
    #     print(f'{f.x=}')
    #
    #     t += dt
    run_kalman_experiment()
