from abstract_pid.pid import TargetProvider


class TargetProviderFromFunction(TargetProvider):
    def __init__(self, fun):
        self.fun = fun

    def get_target(self, t: float) -> float:
        return self.fun(t)


class ConstantTargetProvider(TargetProvider):
    def __init__(self, target: float):
        self.target = target

    def get_target(self, t: float) -> float:
        return self.target
