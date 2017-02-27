import ast
import logging
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBPlugin
import time
import urllib3


LOG = logging.getLogger(__name__)


class GraphitePlugin(TimeSeriesDBPlugin):

    def intialize(self):
        self.host = tendrl_ns.config.data['time_series_db_server']
        self.port = tendrl_ns.config.data['time_series_db_port']
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
                return stats.data
            else:
                TendrlPerformanceMonitoringException(
                    'Request status code: %s' % str(
                        data.status_code
                    )
                )
        except (ValueError, Exception) as ex:
            LOG.error('Failed to fetch stats for metric %s of %s using url %s.Error %s ' % (
                metric_name, entity_name, url, str(ex)), exc_info=True)
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_metrics(self, entity_name):
        url = 'http://%s:%s/metrics/index.json' % (self.host, str(self.port))
        try:
            time.sleep(5)
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
            LOG.error('Failed to get metrics for %s.Error %s ' %
                      (entity_name, ex), exc_info=True)

    def destroy(self):
        pass
