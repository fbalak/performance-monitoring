import ast
import logging
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBPlugin
import urllib2


LOG = logging.getLogger(__name__)


class GraphitePlugin(TimeSeriesDBPlugin):

    def intialize(self, config):
        self.host = tendrl_ns.config.data['time_series_db_server']
        self.port = tendrl_ns.config.data['time_series_db_port']
        self.prefix = 'collectd'

    def get_metric_stats(self, entity_name, metric_name, time=None):
        metric_name = '%s.%s' % (entity_name.replace('.', '_'), metric_name)
        target = '%s.%s' % (self.prefix, metric_name)
        if time == 'latest':
            target = "cactiStyle(%s)" % target
        url = 'http://%s:%s/render?target=%s&format=json' % (
            self.host, str(self.port), target)
        try:
            graph_conn = urllib2.urlopen(url)
            data = graph_conn.read()
            return data
        except (ValueError, urllib2.URLError) as ex:
            LOG.error('Failed to fetch stats for metric %s of %s.Error %s ' % (
                metric_name, entity_name, str(ex)), exc_info=True)
            raise ex
        finally:
            graph_conn.close()

    def get_metrics(self, entity_name):
        url = 'http://%s:%s/metrics/index.json' % (self.host, str(self.port))
        try:
            conn = urllib2.urlopen(url)
            data = conn.read()
            metrics = ast.literal_eval(data)
            result = []
            prefix = "%s.%s." % (self.prefix, entity_name.replace('.', '_'))
            split_metrics = []
            for metric in metrics:
                if metric.startswith(prefix):
                    split_metrics = metric.split(prefix)
                    result.append(split_metrics[1])
            return str(result)
        except (ValueError, urllib2.URLError) as ex:
            LOG.error('Failed to get metrics for %s.Error %s ' %
                      (entity_name, ex), exc_info=True)
        finally:
            conn.close()

    def destroy(self):
        pass
