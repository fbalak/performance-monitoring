import ast
import gevent
from gevent import socket
import json
import re
from ruamel import yaml
import time
import urllib3

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.performance_monitoring import constants as \
    pm_consts
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBPlugin


class GraphitePlugin(TimeSeriesDBPlugin):

    def intialize(self):
        self.host = NS.performance_monitoring.config.data[
            'time_series_db_server']
        self.port = NS.performance_monitoring.config.data[
            'time_series_db_port']
        self.carbon_port = NS.performance_monitoring.config.data[
            'carbon_port'
        ]
        self.graphite_sock = socket.socket()
        self.graphite_sock.connect((self.host, int(self.carbon_port)))
        self.http = urllib3.PoolManager()
        self.prefix = 'collectd'

    def get_metric_stats(self, entity_name, metric_name, time_interval=None):
        metric_name = '%s.%s' % (entity_name.replace('.', '_'), metric_name)
        target = '%s.%s' % (self.prefix, metric_name)
        if time_interval == 'latest':
            target = "cactiStyle(%s)" % target
        url = 'http://%s:%s/render?target=%s&format=json' % (
            self.host, str(self.port), target)
        try:
            stats = self.http.request('GET', url, timeout=5)
            if stats.status == 200:
                # TODO(Anmol): remove nulls from graphite data before returning
                # data. Explore the possibility of achieving this using some
                # tuning factor in graphite.
                data = re.sub('\[null, [0-9]+\], ', '', stats.data)
                data = re.sub(', \[null, [0-9]+\]', '', data)
                return data
            else:
                TendrlPerformanceMonitoringException(
                    'Request status code: %s' % str(
                        stats.status
                    )
                )
        except (ValueError, Exception) as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": 'Failed to fetch stats for metric %s'
                                        ' of %s using url. %s' %
                                        (metric_name, entity_name, url),
                             "exception": ex
                             }
                )
            )
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_metrics(self, entity_name):
        url = 'http://%s:%s/metrics/index.json' % (self.host, str(self.port))
        try:
            gevent.sleep(5)
            resp = self.http.request('GET', url, timeout=5)
            if resp.status != 200:
                raise TendrlPerformanceMonitoringException(
                    'Request status code: %s' % str(resp.status_code)
                )
            data = resp.data
            metrics = ast.literal_eval(data)
            result = []
            prefix = "%s.%s." % (self.prefix, entity_name.replace('.', '_'))
            split_metrics = []
            for metric in metrics:
                if metric.startswith(prefix):
                    split_metrics = metric.split(prefix)
                    result.append(split_metrics[1])
            return str(result)
        except (ValueError, Exception) as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": 'Failed to get metrics for %s.' %
                                        entity_name,
                             "exception": ex
                             }
                )
            )

    def push_metrics(self, metric_name, metric_value):
        message = '%s%s%s %s %d\n' % (
            self.prefix,
            self.get_delimeter(),
            metric_name,
            str(metric_value),
            int(time.time())
        )
        self.graphite_sock.sendall(message)

    def get_utilizationtype(self, resource_name, utilization_type):
        return {
            pm_consts.SYSTEM_UTILIZATION: {
                pm_consts.USED: 'gauge-used',
                pm_consts.TOTAL: 'gauge-total',
                pm_consts.PERCENT_USED: 'percent-percent_bytes',
            },
            pm_consts.CLUSTER_UTILIZATION: {
                pm_consts.USED: 'gauge-used',
                pm_consts.TOTAL: 'gauge-total',
                pm_consts.PERCENT_USED: 'percent-percent_bytes',
            },
            pm_consts.CLUSTER_THROUGHPUT: {
                pm_consts.USED: 'gauge-used'
            },
            pm_consts.SYSTEM_THROUGHPUT: {
                pm_consts.USED: 'gauge-used'
            },
            pm_consts.NODE_THROUGHPUT: {
                pm_consts.USED: 'gauge-used'
            }
        }.get(resource_name, {}).get(utilization_type)

    def get_delimeter(self):
        return "."

    def destroy(self):
        self.graphite_sock.close()
