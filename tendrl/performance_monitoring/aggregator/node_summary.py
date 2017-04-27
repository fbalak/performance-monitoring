import datetime
from etcd import EtcdConnectionFailed
from etcd import EtcdKeyNotFound
import gevent
import math
from pytz import utc

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.commons.utils.time_utils import now as tendrl_now

from tendrl.performance_monitoring import constants as \
    pm_consts
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.objects.node_summary \
    import NodeSummary
from tendrl.performance_monitoring.utils import get_latest_stat
from tendrl.performance_monitoring.utils import get_latest_stats


class NodeSummarise(gevent.greenlet.Greenlet):
    def __init__(self):
        super(NodeSummarise, self).__init__()
        self._complete = gevent.event.Event()

    def get_net_host_cpu_utilization(self, node):
        try:
            percent_user = get_latest_stat(node, 'cpu.percent-user')
            percent_system = get_latest_stat(node, 'cpu.percent-system')
            return {
                'percent_used': str(percent_user + percent_system),
                'updated_at': datetime.datetime.now().isoformat()
            }
        except TendrlPerformanceMonitoringException:
            # Exception already handled
            return None

    def get_net_host_memory_utilization(self, node):
        try:
            used = get_latest_stat(node, 'memory.memory-used')
            total = get_latest_stat(node, 'aggregation-memory-sum.memory')
            percent_used = get_latest_stat(node, 'memory.percent-used')
            return {
                'used': str(used),
                'percent_used': str(percent_used),
                'total': str(total),
                'updated_at': datetime.datetime.now().isoformat()
            }
        except TendrlPerformanceMonitoringException:
            # Exception already handled
            return None

    def get_net_storage_utilization(self, node):
        try:
            used_stats = get_latest_stats(node, 'df-*.df_complex-used')
            used = 0.0
            for stat in used_stats:
                if not math.isnan(float(stat)):
                    used = used + float(stat)
            free_stats = get_latest_stats(node, 'df-*.df_complex-free')
            free = 0.0
            for stat in free_stats:
                if not math.isnan(float(stat)):
                    free = free + float(stat)
            if free + used == 0:
                return None
            percent_used = float(used * 100) / float(free + used)
            return {
                'used': str(used),
                'total': str(used + free),
                'percent_used': str(percent_used),
                'updated_at': datetime.datetime.now().isoformat()
            }
        except TendrlPerformanceMonitoringException:
            # Exception already handled
            return None

    def get_alert_count(self, node):
        try:
            alert_ids = NS.central_store_thread.get_node_alert_ids(node)
            return len(alert_ids)
        except TendrlPerformanceMonitoringException:
            return 0

    def calculate_host_summary(self, node):
        gevent.sleep(0.1)
        cpu_usage = self.get_net_host_cpu_utilization(node)
        memory_usage = self.get_net_host_memory_utilization(node)
        storage_usage = self.get_net_storage_utilization(node)
        alert_count = self.get_alert_count(node)
        old_summary = NodeSummary(
            node_id=node,
            name='',
            status='',
            role='',
            cluster_name='',
            cpu_usage={
                'percent_used': '',
                'updated_at': ''
            },
            memory_usage={
                'percent_used': '',
                'updated_at': '',
                'used': '',
                'total': ''
            },
            storage_usage={
                'percent_used': '',
                'total': '',
                'used': '',
                'updated_at': ''
            },
            alert_count=alert_count
        )
        try:
            old_summary = old_summary.load()
        except EtcdKeyNotFound:
            pass
        except (EtcdConnectionFailed, Exception) as ex:
            Event(
                ExceptionMessage(
                    priority="debug",
                    publisher=NS.publisher_id,
                    payload={"message": 'Failed to fetch previously computed '
                                        'summary from etcd.',
                             "exception": ex
                             }
                )
            )
            return
        if cpu_usage is None:
            cpu_usage = old_summary.cpu_usage
        if memory_usage is None:
            memory_usage = old_summary.memory_usage
        if storage_usage is None:
            storage_usage = old_summary.storage_usage
        try:
            summary = NodeSummary(
                name=NS.central_store_thread.get_node_name_from_id(node),
                node_id=node,
                status=self.get_node_status(node),
                role=NS.central_store_thread.get_node_role(node),
                cluster_name=NS.central_store_thread.get_node_cluster_name(
                    node
                ),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                storage_usage=storage_usage,
                alert_count=alert_count
            )
            summary.save(update=False)
        except Exception as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": 'Exception caught while trying to '
                                        'save summary for node %s' % str(node),
                             "exception": ex
                             }
                )
            )

    def get_node_status(self, node_id):
        last_seen_at = NS.central_store_thread.get_node_last_seen_at(node_id)
        if last_seen_at:
            interval = (
                tendrl_now() -
                datetime.datetime.strptime(
                    last_seen_at[:-6],
                    "%Y-%m-%dT%H:%M:%S.%f"
                ).replace(tzinfo=utc)
            ).total_seconds()
            if interval < 5:
                return pm_consts.STATUS_UP
            else:
                return pm_consts.STATUS_DOWN
        return pm_consts.STATUS_NOT_MONITORED

    def calculate_host_summaries(self):
        nodes = NS.central_store_thread.get_node_ids()
        for node in nodes:
            self.calculate_host_summary(node)

    def _run(self):
        while not self._complete.is_set():
            self.calculate_host_summaries()
            gevent.sleep(60)

    def stop(self):
        self._complete.set()
