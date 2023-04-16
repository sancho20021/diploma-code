class ControlledObject:
    def set_input(self, x: float, t: float):
        pass

    def get_output(self, t: float) -> float:
        pass


class SimoControlledObject:
    def get_input(self, t: float):
        pass

    def set_input(self, x: float, t: float):
        pass

    def get_output(self, name: str, t: float) -> float:
        pass


class TargetProvider:
    def get_target(self, t: float) -> float:
        pass


class PID:
    """
    Его запускают строго раз в period секунд
    """

    def __init__(
        self,
        k_p: float,
        k_i: float,
        k_d: float,
        controlled_object: ControlledObject,
        target_provider: TargetProvider,
        period: float
    ):
        self.period = period

        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d

        self.controlled_object = controlled_object
        self.target_provider = target_provider

        self.e_prev = 0
        self.sum_e_prev = 0
        self.input_copy = 0

    def _pid(self, e: float) -> float:
        return self.k_p * e \
            + self.k_d / self.period * (e - self.e_prev) \
            + self.k_i * self.period * (self.sum_e_prev + e)

    def do(self, t):
        target = self.target_provider.get_target(t)
        actual = self.controlled_object.get_output(t)

        e = target - actual
        u = self._pid(e)
        print(f'{target=}, {actual=}, {e=}, {u=}')

        # if self.e_prev < 0 < e or self.e_prev > 0 > e:
        #     self.sum_e_prev = 0
        #     print('error crossed zero, setting sum to 0')

        self.e_prev = e
        self.sum_e_prev += e
        print(f'{self.sum_e_prev=}')

        # print(f'error={e}, sum_error = {self.sum_e_prev}, u={u}')

        self.controlled_object.set_input(u, t)
        self.input_copy = input
        # print(f'new_input={input}')
