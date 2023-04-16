from abstract_pid.pid import Driver


class IdentityDriver(Driver):
    def convert_to_input(self, x) -> float:
        return x
