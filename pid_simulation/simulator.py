class Event:
    def __init__(self, process, scheduled_time):
        self.process = process
        self.scheduled_time = scheduled_time


class Simulator:
    def __init__(self, processes):
        self.processes = processes

    def simulate(self, time):
        t = 0
        events = [Event(process, 0) for process in self.processes]

        while t < time:
            next_event = min(events, key=lambda ev: ev.scheduled_time)
            assert next_event.scheduled_time >= t
            t = next_event.scheduled_time
            next_event.process.do(t)

            assert next_event.process.period > 0
            # period may change
            next_event.scheduled_time = t + next_event.process.period



