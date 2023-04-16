from task_model import (
    IntervalStorage, S3, TaskExecutor, SoftResourceProvider
)


# Раз в period квантов времени замеряет показатели s3 usage, demand, interval
class Logger:
    def __init__(self, period: float, interval: IntervalStorage, s3: S3, task_executor: TaskExecutor, output_lines):
        self.period = period
        self.interval = interval
        self.s3 = s3
        self.task_executor = task_executor
        self.output_lines = output_lines

    def do(self, t):
        self.task_executor.clear_finished(t)
        message = {
            'interval': self.interval.get(),
            's3_usage': self.s3.get_usage(),
            's3_limit': self.s3.get_capacity()
        }
        self.output_lines.append(message)
        print(message)


class SoftResourceLogger:
    def __init__(self, period: float, res_provider: SoftResourceProvider, output_lines):
        self.period = period
        self.res_provider = res_provider
        self.output_lines = output_lines

    def do(self, t):
        message = {
            'usage': self.res_provider.usage,
            'demand': self.res_provider.demand,
            'actual_limit': self.res_provider.capacity_fun(t)
        }
        self.output_lines.append(message)
        print(message)
