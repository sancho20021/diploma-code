from abstract_pid.pid import (
    ControlledObject, TargetProvider, PID, SimoControlledObject,
)
from abstract_pid.multi_pid import (MultiPid, AggregatingPid)


class Logger:
    def __init__(
        self,
        controlled_object: ControlledObject,
        target_provider: TargetProvider,
        pid: PID,
        output_lines,
        period: float
    ):
        self.period = period
        self.controlled_object = controlled_object
        self.target_provider = target_provider
        self.pid = pid
        self.output_lines = output_lines

    def do(self, t):
        actual_output = self.controlled_object.get_output(t)
        target_output = self.target_provider.get_target(t)
        input = self.pid.input_copy
        record = {
            'actual_output': actual_output,
            'target_output': target_output,
            'input': input,
            'time': t
        }
        self.output_lines.append(record)
        print(record)


class MultiPidLogger:
    def __init__(
        self,
        pid: MultiPid,
        output_lines,
        period: float
    ):
        self.period = period
        self.pid = pid
        self.output_lines = output_lines

    def do(self, t):
        record = {}

        my_input = self.pid.input_copy
        record['input'] = my_input
        record['time'] = t
        for name, pid in self.pid.pids.items():
            output = pid.controlled_object.get_output(t)
            target_output = pid.target_provider.get_target(t)

            record[name] = {
                'output': output,
                'target_output': target_output
            }

        self.output_lines.append(record)
        print(record)


class AggregatingLogger:
    def __init__(
        self,
        pid: AggregatingPid,
        output_lines,
        period: float
    ):
        self.period = period
        self.pid = pid
        self.output_lines = output_lines

    def do(self, t):
        record = {}

        my_input = self.pid.input_copy
        record['input'] = self.pid.simo_co.get_input(t)
        record['time'] = t
        for name, target_provider in self.pid.target_providers.items():
            target_output = target_provider.get_target(t)
            real_output = self.pid.simo_co.get_output(name, t)
            record[name] = {
                'output': real_output,
                'target_output': target_output
            }

        self.output_lines.append(record)
        print(record)
