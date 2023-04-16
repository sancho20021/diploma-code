import numpy as np
from typing import Callable

from abstract_pid.pid import (ControlledObject, SimoControlledObject)


def simple_linear(k: float, b: float):
    return lambda x: k * x + b


class SimpleLinear(ControlledObject):
    def __init__(self, k: float, b: float):
        self.k = k
        self.b = b
        self.input = 0

    def set_input(self, x: float, t: float):
        self.input = x

    def get_output(self, t: float) -> float:
        return self.k * self.input + self.b


class NoisedLinear(ControlledObject):
    def __init__(self, k: float, b: float, deviation: float):
        self.k = k
        self.b = b
        self.input = 0
        self.deviation = deviation

    def set_input(self, x: float, t: float):
        self.input = x

    def get_output(self, t: float) -> float:
        return np.random.normal(self.k * self.input + self.b, self.deviation)


class MultiFunSimoCO(SimoControlledObject):
    def __init__(self, funs: dict[str, Callable[[float], float]]):
        self.funs = funs
        self.input = 0

    def get_input(self, t: float):
        return self.input

    def set_input(self, x: float, t: float):
        self.input = x

    def get_output(self, name: str, t: float) -> float:
        return self.funs[name](self.get_input(t))
