import ast
import time
import urllib3

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage

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

    def destroy(self):
        pass
