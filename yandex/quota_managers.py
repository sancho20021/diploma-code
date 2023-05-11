import dataclasses
import logging
from abc import ABC, abstractmethod

from datetime import datetime, timedelta
from typing import List, Optional

from ott.drm.library.python.packager_task.clients import PackagerTasksApiClient
from ott.drm.library.python.packager_task.models import TaskStatus, PackagerTask
from yweb.video.faas.graphs.ott.common import Priority
from yt.wrapper import YtClient


class QuotaManager(ABC):
    def __init__(
        self,
        tasks_client: PackagerTasksApiClient,
        nirvana_quota: str,
        vod_providers: List[str],
        parallel_graph_launch_delay_sec: int
    ):
        self.tasks_client = tasks_client
        self.nirvana_quota = nirvana_quota
        self.vod_providers = vod_providers
        self.parallel_graph_launch_delay_sec = parallel_graph_launch_delay_sec

    @abstractmethod
    def available_slots(self) -> int:
        pass

    def can_launch_parallel_graph(self) -> bool:
        recent_parallel_graphs_cnt = self.tasks_client.count(
            [TaskStatus.PACKAGING],
            nirvana_quota=self.nirvana_quota,
            vod_providers=self.vod_providers,
            parallel_encoding=True,
            update_time_lower_bound=datetime.utcnow() - timedelta(seconds=self.parallel_graph_launch_delay_sec)
        )

        return recent_parallel_graphs_cnt == 0

    def filter_tasks_to_launch(self, tasks: list[PackagerTask]) -> list[PackagerTask]:
        max_priority_tasks = [
            task
            for task in tasks
            if task.priority == Priority.MAX
        ]
        other_tasks = [
            task
            for task in tasks
            if task.priority != Priority.MAX
        ]
        if not other_tasks:
            return max_priority_tasks

        can_launch_parallel_graph = self.can_launch_parallel_graph()

        can_launch = self.available_slots()
        tasks_to_launch = max_priority_tasks
        can_launch -= len(max_priority_tasks)
        for task in list(other_tasks):
            if can_launch <= 0:
                break

            if task.is_parallel_encoding():
                if not can_launch_parallel_graph:
                    logging.info(f'Parallel encoding quota limit is reached! '
                                 f'Task {task} will be launched later')
                    continue

                can_launch_parallel_graph = False

            other_tasks.remove(task)
            tasks_to_launch.append(task)
            can_launch -= 1

        if other_tasks:
            logging.info('Quota limit is reached!')
            logging.debug(f'Tasks({len(other_tasks)}): {other_tasks} will be launched later')

        return tasks_to_launch


@dataclasses.dataclass
class ResourcesData:
    ram: float
    cpu: float


@dataclasses.dataclass
class DemandUsageData:
    usage: ResourcesData
    demand: ResourcesData


class ResourceQuotaManager(QuotaManager):
    """
    Attributes:
        step: The number of graphs to launch when demand = usage
        max_demand_usage_diff: The maximum difference between resource demand and usage (usually in [0..1]).
    """

    def __init__(
        self,
        max_demand_usage_diff: float,
        step: int,
        tasks_client: PackagerTasksApiClient,
        yt_client: YtClient,
        nirvana_quota: str,
        vod_providers: List[str],
        parallel_graph_launch_delay_sec: int,
    ):
        super().__init__(tasks_client, nirvana_quota, vod_providers, parallel_graph_launch_delay_sec)
        self.yt_client = yt_client
        self.max_demand_usage_diff = max_demand_usage_diff
        self.step = step

    def available_slots(self) -> int:
        yt = self._get_demand_usage()
        if yt is None:
            logging.error("Can't get YT resource usage or demand. Not launching tasks.")
            return 0
        if yt.demand.cpu < yt.usage.cpu or yt.demand.ram < yt.usage.ram:
            logging.error("YT demand < usage (strange response). Still launching tasks.")
            return self.step

        if yt.usage.ram == 0 or yt.usage.cpu == 0:
            return self.step
        if self.max_demand_usage_diff <= 0:
            # Может быть можно провалидировать параметр во время создания таски?
            logging.error("max demand - usage diff is less or equal to 0 (invalid value). Not launching tasks.")
            return 0

        ram_coef = yt.demand.ram / yt.usage.ram
        cpu_coef = yt.demand.cpu / yt.usage.cpu

        max_coef = 1 + self.max_demand_usage_diff
        limiting_resource, cur_coef = max([('ram', ram_coef), ('cpu', cpu_coef)], key=lambda p: p[1])

        # rounding half up, so when the cur_coef is 1.001, slots is equal to step
        slots = max(0, round(self.step * (max_coef - cur_coef) / (max_coef - 1)))
        if slots == 0:
            logging.warning(
                f'{limiting_resource} demand/usage reached {cur_coef}, which is too close / above {max_coef} limit.\n'
                f'Not launching tasks.')
        logging.debug(
            f'ResourceQuota: '
            f'{slots=} '
            f'{limiting_resource=} '
            f'{cur_coef=} '
            f'{max_coef=} '
        )

        return slots

    def _get_demand_usage(self) -> Optional[DemandUsageData]:
        table = '//sys/scheduler/orchid/scheduler/scheduling_info_per_pool_tree/physical/fair_share_info/' \
                f'pools/nirvana-{self.nirvana_quota}'
        try:
            row = self.yt_client.get(table)
        except Exception as e:
            logging.error(f"Error while getting yt table: {e}")
            return

        try:
            return DemandUsageData(
                usage=ResourcesData(ram=row['resource_usage']['user_memory'], cpu=row['resource_usage']['cpu']),
                demand=ResourcesData(ram=row['resource_demand']['user_memory'], cpu=row['resource_demand']['cpu'])
            )
        except KeyError as e:
            logging.error(f"Error '{e}' while parsing yt response:\n{row}")
            return
