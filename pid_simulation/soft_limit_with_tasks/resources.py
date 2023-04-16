# Assume that if task started, it continues to execute no matter what capacity of resources is
class SoftResourceProvider:
    def __init__(self, capacity_fun):
        self.capacity_fun = capacity_fun
        self.usage = 0

    def try_alloc(self, t, x) -> bool:
        if self.usage + x <= self.capacity_fun(t):
            self.usage += x
            return True
        else:
            return False

    def free(self, t, x):
        assert x > 0
        self.usage = max(0, self.usage - x)

    def limit_exceeded(self, t) -> bool:
        return self.usage > self.capacity_fun(t)
