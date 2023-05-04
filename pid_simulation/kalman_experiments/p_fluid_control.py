import json
from pathlib import Path

from kalman_experiments import Barrel, LChanger
from simulator import Simulator


class ProportionalInputController:
    def __init__(self, barrel: Barrel, k_p: float):
        self.barrel = barrel
        self.period = barrel.period
        self.k_p = k_p

    def do(self, t: float):
        self.barrel.v = self.k_p * self.barrel.d


class Logger:
    def __init__(self, barrel: Barrel, output_lines: list[dict]):
        self.barrel = barrel
        self.period = barrel.period
        self.output_lines = output_lines

    def do(self, t: float):
        d = self.barrel.d
        v = self.barrel.v
        real_l = self.barrel.l
        data = {'d': d, 'v': v, 'l_actual': real_l, 't': t}
        print(f'{t=}, {data=}')
        self.output_lines.append(data)


def run_p_control(k_p: float):
    output_file = Path(f'./logs/p_control_{k_p}.json')
    output_lines = []

    def l_fun(t: float) -> float:
        if 20 < t < 40:
            return 10
        else:
            return 5

    period = 1
    duration = period * 70

    barrel = Barrel(7, l_fun(0), period)
    l_changer = LChanger(barrel, l_fun)
    logger = Logger(barrel, output_lines)
    controller = ProportionalInputController(barrel, k_p)
    simulator = Simulator([barrel, l_changer, controller, logger])
    simulator.simulate(duration)

    with open(output_file, mode='w') as file:
        for line in output_lines:
            file.write(f'{json.dumps(line)}\n')
    print('ready')


if __name__ == '__main__':
    run_p_control(-0.5)
    run_p_control(-1)
    run_p_control(-2)
    run_p_control(-2.01)
    # run_p_control(-4)
    # run_p_control(-8)
    # run_p_control(-16)