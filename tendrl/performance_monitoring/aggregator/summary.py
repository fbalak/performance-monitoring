import datetime
from etcd import EtcdConnectionFailed
from etcd import EtcdKeyNotFound
import logging
import multiprocessing
import re
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.objects.summary \
    import PerformanceMonitoringSummary
import time
import urllib2

LOG = logging.getLogger(__name__)


class Summarise(multiprocessing.Process):
    def __init__(self, timeSeriesDbManager):
        super(Summarise, self).__init__()
        self._complete = multiprocessing.Event()
        self.time_series_db_manager = timeSeriesDbManager

    ''' Get latest stats of resource as in param resource'''
    def get_latest_stat(self, node, resource):
        try:
            node_name = tendrl_ns.central_store_thread.get_node_name_from_id(
                node
            )
            stats = self.time_series_db_manager.get_plugin().get_metric_stats(
                node_name,
                resource,
                'latest'
            )
            return float(re.search('Current:(.+?)Max', stats).group(1))
        except (ValueError, urllib2.URLError, AttributeError) as ex:
            LOG.debug(
                'Failed to get latest stat of %s of node %s for node summary.'
                'Error %s'
                % (resource, node, str(ex)),
                exc_info=True
            )
            raise TendrlPerformanceMonitoringException(ex)

    ''' Get latest stats of resources matching wild cards in param resource'''
    def get_latest_stats(self, node, resource):
        try:
            node_name = tendrl_ns.central_store_thread.get_node_name_from_id(node)
            stats = self.time_series_db_manager.get_plugin().get_metric_stats(
                node_name,
                resource,
                'latest'
            )
            return re.findall('Current:(.+?)Max', stats)
        except (ValueError, urllib2.URLError, AttributeError) as ex:
            LOG.debug(
                'Failed to get latest stats of %s of node %s for node summary'
                'Error %s' % (resource, node, str(ex)),
                exc_info=True
            )
            raise TendrlPerformanceMonitoringException(ex)

    def get_net_host_cpu_utilization(self, node):
        try:
            percent_user = self.get_latest_stat(node, 'cpu.percent-user')
            percent_system = self.get_latest_stat(node, 'cpu.percent-system')
            return {
                'percent_used': (percent_user + percent_system),
                'updated_at': datetime.datetime.now().isoformat()
            }
        except TendrlPerformanceMonitoringException:
            # Exception already handled
            return None

    def get_net_host_memory_utilization(self, node):
        try:
            used = self.get_latest_stat(node, 'memory.memory-used')
            total = self.get_latest_stat(node, 'aggregation-memory-sum.memory')
            percent_used = self.get_latest_stat(node, 'memory.percent-used')
            return {
                'used': used,
                'percent_used': percent_used,
                'total': total,
                'updated_at': datetime.datetime.now().isoformat()
            }
        except TendrlPerformanceMonitoringException:
            # Exception already handled
            return None

    def get_net_storage_utilization(self, node):
        try:
            used_stats = self.get_latest_stats(node, 'df-*.df_complex-used')
            used = 0.0
            for stat in used_stats:
                used = used + float(stat)
            free_stats = self.get_latest_stats(node, 'df-*.df_complex-free')
            free = 0.0
            for stat in free_stats:
                free = free + float(stat)
            if free + used == 0:
                return None
            percent_used = float(used * 100) / float(free + used)
            return {
                'used': used,
                'total': used + free,
                'percent_used': percent_used,
                'updated_at': datetime.datetime.now().isoformat()
            }
        except TendrlPerformanceMonitoringException:
            # Exception already handled
            return None

    def calculate_host_summary(self, node):
        cpu_usage = self.get_net_host_cpu_utilization(node)
        memory_usage = self.get_net_host_memory_utilization(node)
        storage_usage = self.get_net_storage_utilization(node)
        alert_count = len(tendrl_ns.central_store_thread.get_alerts(node))
        old_summary = PerformanceMonitoringSummary(
            node,
            cpu_usage={
                'percent_used': None,
                'updated_at': None
            },
            memory_usage={
                'percent_used': None,
                'updated_at': None,
                'used': None,
                'total': None
            },
            storage_usage={
                'percent_used': None,
                'total': None,
                'used': None,
                'updated_at': None
            },
            alert_count=0
        )
        try:
            tendrl_ns.etcd_orm.client.read(old_summary.value)
            old_summary = old_summary.load()
        except EtcdKeyNotFound:
            pass
        except EtcdConnectionFailed as ex:
            LOG.error(
                'Failed to fetch previously computed summary from etcd.'
                'Error %s' % str(ex),
                exc_info=True
            )
            return
        if cpu_usage is None:
            cpu_usage = old_summary.cpu_usage
        if memory_usage is None:
            memory_usage = old_summary.memory_usage
        if storage_usage is None:
            storage_usage = old_summary.storage_usage
        tendrl_ns.summary = \
            tendrl_ns.performance_monitoring.objects.\
            PerformanceMonitoringSummary(
                node,
                cpu_usage,
                memory_usage,
                storage_usage,
                alert_count
            )
        tendrl_ns.summary.save()

    def calculate_host_summaries(self):
        nodes = tendrl_ns.central_store_thread.get_node_ids()
        for node in nodes:
            self.calculate_host_summary(node)

    def run(self):
        while not self._complete.is_set():
            self.calculate_host_summaries()
            time.sleep(60)

    def stop(self):
        self._complete.set()
