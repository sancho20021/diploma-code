import dataclasses
import json


@dataclasses.dataclass
class UtilizationRecord:
    usage: float
    demand: float
    actual_limit: float
    time: float

    @property
    def __dict__(self):
        return dataclasses.asdict(self)

    @property
    def json(self):
        return json.dumps(self.__dict__)