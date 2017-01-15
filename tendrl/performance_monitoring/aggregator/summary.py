import datetime
import logging
import multiprocessing
import re
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
import time
import urllib2

LOG = logging.getLogger(__name__)


class Summarise(multiprocessing.Process):
    def __init__(self, persister_instance, timeSeriesDbManager):
        super(Summarise, self).__init__()
        self._complete = multiprocessing.Event()
        self._persister = persister_instance
        self.time_series_db_manager = timeSeriesDbManager

    def get_latest_stat(self, node, resource):

        '''
            Get latest stats of resource as in param resource
            Keyword arguments:
            node: The id of node of which the latest stats are required
            resource: The name of resource
            Returns:
            Latest stat of float type
        '''

        try:
            node_name = self._persister.get_node_name_from_id(node)
            stats = self.time_series_db_manager.get_plugin().get_metric_stats(
                node_name,
                resource,
                'latest'
            )
            return float(re.search('Current:(.+?)Max', stats).group(1))
        except (ValueError, urllib2.URLError, AttributeError) as ex:
            LOG.error(
                'Failed to get latest stat of %s of node %s for node summary.'
                'Error %s'
                % (resource, node, str(ex)),
                exc_info=True
            )
            raise TendrlPerformanceMonitoringException(ex)

    def get_latest_stats(self, node, resource):

        '''
            Get latest stats of resources matching wild cards in param resource
            Keyword arguments:
            node: The id of node of which the latest stats are required
            resource: The pattern of resource name including wild cards
            Returns:
            Array of latest stats
        '''

        try:
            node_name = self._persister.get_node_name_from_id(node)
            stats = self.time_series_db_manager.get_plugin().get_metric_stats(
                node_name,
                resource,
                'latest'
            )
            return re.findall('Current:(.+?)Max', stats)
        except (ValueError, urllib2.URLError, AttributeError) as ex:
            LOG.error(
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
            percent_used = self.get_latest_stat(node, 'memory.percent-used')
            return {
                'used': used,
                'percent_used': percent_used,
                'total': (used * 100) / percent_used,
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
        try:
            summary = self._persister.get_node_summary(node)
            if summary is None:
                summary = {}
            net_cpu_utilization = self.get_net_host_cpu_utilization(node)
            if net_cpu_utilization is not None:
                summary['cpu'] = net_cpu_utilization
            net_memory_utilization = self.get_net_host_memory_utilization(node)
            if net_memory_utilization is not None:
                summary['memory'] = net_memory_utilization
            net_storage_utilization = self.get_net_storage_utilization(node)
            if net_storage_utilization is not None:
                summary['storage'] = net_storage_utilization
            alert_count = len(self._persister.get_alerts(node))
            if alert_count is not None:
                summary['alert_cnt'] = alert_count
            if summary:
                self._persister.save_node_summary(summary, node)
        except TendrlPerformanceMonitoringException as ex:
            LOG.error(
                'Exception %s caught while calculating summary for node %s' % (
                    str(ex),
                    node
                ), exc_info=True
            )

    def calculate_host_summaries(self):
        nodes = self._persister.get_node_ids()
        for node in nodes:
            self.calculate_host_summary(node)

    def run(self):
        while not self._complete.is_set():
            time.sleep(60)
            self.calculate_host_summaries()

    def stop(self):
        self._complete.set()
