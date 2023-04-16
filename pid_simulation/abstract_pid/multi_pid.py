import dataclasses
from typing import Dict

from abstract_pid.pid import (
    PID, ControlledObject, TargetProvider, SimoControlledObject
)

from abstract_pid.target_providers import ConstantTargetProvider


@dataclasses.dataclass
class PidConfig:
    target_provider: TargetProvider
    k_p: float
    k_i: float
    k_d: float


class BoxControlledObject(ControlledObject):
    def __init__(self):
        self.input = 0
        self.output = 0

    def set_input(self, x: float, t: float):
        self.input = x

    def get_output(self, t: float) -> float:
        return self.output

    def set_output(self, x: float):
        self.output = x


class MultiPid:
    def __init__(
        self,
        simo_control_object: SimoControlledObject,
        pid_configs: Dict[str, PidConfig],
        period: float
    ):
        self.period = period

        self.simo_control_object = simo_control_object

        self.input_copy = 0

        self.pids: Dict[str, PID] = dict()
        self.control_objects: Dict[str, BoxControlledObject] = dict()

        for name, config in pid_configs.items():
            co = BoxControlledObject()
            self.control_objects[name] = co
            pid = PID(controlled_object=co, target_provider=config.target_provider, period=period,
                      k_i=config.k_i, k_p=config.k_p, k_d=config.k_d)
            self.pids[name] = pid

    def do(self, t):
        print(f'multipid iteration, {t=}')

        # save input copy
        print(f'setting input copy of simo to {self.simo_control_object.get_input(t)}')
        self.input_copy = self.simo_control_object.get_input(t)

        # set outputs for each pid, so they have current state (RAM demand, CPU demand, etc)
        for name, co in self.control_objects.items():
            print(f'setting output of {name} to {self.simo_control_object.get_output(name, t)}')
            co.set_output(self.simo_control_object.get_output(name, t))

        # iterate each pid, so we have new suggested input signals
        print(f'iterating all pids')
        for name, pid in self.pids.items():
            print(f'--------pid {name} start-------')
            pid.do(t)
            print(f'pid {name}: input = {self.control_objects[name].input}')
            print(f'--------pid {name} end-------\n')

        # get minimal suggested input signal from proxy controlled objects
        min_signal_pid = min(self.pids.keys(), key=lambda co_name: self.control_objects[co_name].input)

        print(f'pid {min_signal_pid} is active')

        # set every inactive pid's sum error to zero
        for name, pid in self.pids.items():
            if name == min_signal_pid:
                continue

            print(f'setting {name} pids sum_e to 0')
            pid.sum_e_prev = 0

        # set main and all others input signal to active pid's suggested input
        min_input = self.control_objects[min_signal_pid].input
        print(f'setting input to {min_input}')
        self.simo_control_object.set_input(min_input, t)
        for name, co in self.control_objects.items():
            co.set_input(min_input, t)


class AggregatingPid:
    def __init__(
        self,
        simo_control_object: SimoControlledObject,
        target_providers: Dict[str, TargetProvider],
        k_p: float,
        k_i: float,
        k_d: float,
        period: float
    ):
        self.simo_co = simo_control_object
        self.target_providers = target_providers
        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d
        self.period = period

        self.proxy_co = BoxControlledObject()
        self.pid = PID(k_p=k_p, k_i=k_i, k_d=k_d, controlled_object=self.proxy_co,
                       target_provider=ConstantTargetProvider(0),
                       period=period)
        self.input_copy = 0

    def do(self, t):
        print(f'aggregating pid iteration, {t=}')

        # save input copy
        print(f'setting input copy of simo to {self.simo_co.get_input(t)}')
        self.input_copy = self.simo_co.get_input(t)

        # set outputs for pid
        errors_absolute = {
            name: self.target_providers[name].get_target(t) - self.simo_co.get_output(name, t)
            for name in self.target_providers.keys()
        }
        errors_relative = {
            name: error / self.target_providers[name].get_target(t) if self.target_providers[name].get_target(
                t) != 0 else 1
            for name, error in errors_absolute.items()
        }
        print(f'{errors_relative=}')
        min_error_output_name = min(errors_relative.keys(), key=lambda co_name: errors_relative[co_name])
        min_error = errors_relative[min_error_output_name]

        print(f'min error is {min_error_output_name}, it is {min_error}')
        print(f'setting output of PID to {min_error}')
        self.proxy_co.set_output(min_error)

        # iterate pid
        print(f'-------iterating pid start-------')
        self.pid.do(t)
        print(f'suggested input = {self.proxy_co.input}')
        print(f'-------iterating pid end-------\n')

        print(f'setting simo input to {self.proxy_co.input}')
        self.simo_co.set_input(self.proxy_co.input, t)
