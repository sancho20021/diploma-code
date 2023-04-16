import json
import dataclasses
from records_replica import UtilizationRecord
import math


@dataclasses.dataclass
class AverageDiffMetric:
    average_usage_util: float
    average_demand_util: float
    sum_of_deltas: float
    demand_dev: float

    @property
    def __dict__(self):
        return dataclasses.asdict(self)

    @property
    def json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def calculate(records: list[UtilizationRecord]):
        usage_util = sum([x.usage / x.actual_limit for x in records]) / len(records)
        demand_util = sum([x.demand / x.actual_limit for x in records]) / len(records)
        
        demand_mean = sum([x.demand for x in records]) / len(records)
        demand_dev = math.sqrt(sum([(x.demand - demand_mean) ** 2 for x in records]) / len(records))
        
        sum_of_deltas = abs(usage_util - 1) + abs(demand_util - 1)
        return AverageDiffMetric(
            average_usage_util=usage_util,
            average_demand_util=demand_util,
            sum_of_deltas=sum_of_deltas,
            demand_dev=demand_dev
        )
    
    
@dataclasses.dataclass
class AdaptingSpeedMetric:
    time_to_ascend: float
    time_to_descend: float
    sum_of_times: float

    @property
    def __dict__(self):
        return dataclasses.asdict(self)

    @property
    def json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def calculate(records: list[UtilizationRecord]):
        limit_values = list(sorted(list(set([record.actual_limit for record in records]))))
        if len(limit_values) != 2:
            return None
        if not ((records[0].actual_limit == limit_values[0] and records[-1].actual_limit == limit_values[0])):
            return None
        ascend_i = 0
        while records[ascend_i].actual_limit == limit_values[0]:
            ascend_i += 1
            
        descend_i = ascend_i
        while records[descend_i].actual_limit == limit_values[1]:
            descend_i += 1
            
        ascend_start = records[ascend_i].time
        descend_start = records[descend_i].time
        
        reached_limit = ascend_i
        while records[reached_limit].demand < limit_values[1]:
            reached_limit += 1
        reached_time = records[reached_limit].time - ascend_start
        
        reached_drop = descend_i
        while records[reached_drop].demand > limit_values[0] and records[reached_drop].demand >= records[reached_drop + 1].demand:
            reached_drop += 1
        reached_drop_time = records[reached_drop].time - descend_start
        
        return AdaptingSpeedMetric(time_to_ascend=reached_time, time_to_descend=reached_drop_time, sum_of_times=reached_time+reached_drop_time)
