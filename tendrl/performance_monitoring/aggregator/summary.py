import ast
import datetime
import etcd
import json
import logging
import multiprocessing
import re
from tendrl.common.config import ConfigNotFound
from tendrl.common.config import TendrlConfig
from tendrl.common.etcdobj.etcdobj import Server as etcd_server
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBManager
import time
import urllib2

LOG = logging.getLogger(__name__)
config = TendrlConfig()


class Summarise(multiprocessing.Process):
    def __init__(self):
        super(Summarise, self).__init__()
        self._complete = multiprocessing.Event()
        etcd_kwargs = {
            'port': int(config.get("common", "etcd_port")),
            'host': config.get("common", "etcd_connection")
        }
        self.etcd_client = etcd_server(etcd_kwargs=etcd_kwargs).client

    def get_node_name_from_id(self, node_id):
        try:
            node_name_path = '/nodes/%s/Node_context/fqdn' % node_id
            return self.etcd_client.read(node_name_path).value
        except (
            ConfigNotFound,
            etcd.EtcdKeyNotFound,
            etcd.EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            etcd.EtcdException,
            TypeError
        ) as ex:
            raise ex

    def get_node_ids(self):
        try:
            nodes = self.etcd_client.read(
                '/nodes',
                recursive=True
            )
            node_ids = []
            for child in nodes._children:
                for node in child['nodes']:
                    for _node in node['nodes']:
                        if _node['key'].endswith('Node_context/node_id'):
                            node_ids.append(_node['value'])
            return node_ids
        except etcd.EtcdKeyNotFound:
            return []
        except (
            ConfigNotFound,
            etcd.EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            TypeError
        ) as ex:
            LOG.error(
                'Failed to get nodes from etcd. Error %s' % str(ex),
                exc_info=True
            )
            raise TendrlPerformanceMonitoringException(ex)

    def get_latest_stat(self, node, resource):
        try:
            node_name = self.get_node_name_from_id(node)
            stats = TimeSeriesDBManager().get_plugin().get_metric_stats(
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
        try:
            node_name = self.get_node_name_from_id(node)
            stats = TimeSeriesDBManager().get_plugin().get_metric_stats(
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
            # Exception already handle_data
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
            # Exception already handle_data
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
            # Exception already handle_data
            return None

    def get_alerts(self, node_ids):
        alerts_arr = []
        try:
            alerts = self.etcd_client.read('/alerts', recursive=True)
        except etcd.EtcdKeyNotFound:
            return alerts_arr
        except (
            etcd.EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            TypeError
        ) as ex:
            LOG.error(
                'Failed to fetch alerts. Error %s' % str(ex),
                exc_info=True
            )
            return None
        for child in alerts._children:
            alerts_arr.append(json.loads(child['value']))
        if node_ids is not None:
            filtered_alerts = []
            for alert in alerts_arr:
                if alert['node_id'] in node_ids:
                    filtered_alerts.append(alert)
            return filtered_alerts
        return alerts_arr

    def calculate_host_summary(self, node):
        summary = {}
        try:
            summary = ast.literal_eval(
                self.etcd_client.read(
                    '/monitoring/summary/%s' % node
                ).value
            )
        except etcd.EtcdKeyNotFound:
            pass
        except (
            etcd.EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            TypeError
        ) as ex:
            LOG.error(
                'Failed to fetch previously stored summary for %s.'
                'Error %s' % (node, ex),
                exc_info=True
            )
            return
        net_cpu_utilization = self.get_net_host_cpu_utilization(node)
        if net_cpu_utilization is not None:
            summary['cpu'] = net_cpu_utilization
        net_memory_utilization = self.get_net_host_memory_utilization(node)
        if net_memory_utilization is not None:
            summary['memory'] = net_memory_utilization
        net_storage_utilization = self.get_net_storage_utilization(node)
        if net_storage_utilization is not None:
            summary['storage'] = net_storage_utilization
        alert_count = len(self.get_alerts(node))
        if alert_count is not None:
            summary['alert_cnt'] = alert_count
        if summary:
            self.etcd_client.write(
                '/monitoring/summary/%s' % node,
                summary
            )

    def calculate_host_summaries(self):
        nodes = self.get_node_ids()
        for node in nodes:
            self.calculate_host_summary(node)

    def run(self):
        while not self._complete.is_set():
            time.sleep(60)
            self.calculate_host_summaries()

    def stop(self):
        self._complete.set()
