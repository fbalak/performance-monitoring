import ast
import logging
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBPlugin
import time
import urllib2


LOG = logging.getLogger(__name__)


class GraphitePlugin(TimeSeriesDBPlugin):

    def intialize(self):
        self.host = tendrl_ns.config.data['time_series_db_server']
        self.port = tendrl_ns.config.data['time_series_db_port']
        self.prefix = 'collectd'

    def get_metric_stats(self, entity_name, metric_name, time_interval=None):
        metric_name = '%s.%s' % (entity_name.replace('.', '_'), metric_name)
        target = '%s.%s' % (self.prefix, metric_name)
        if time_interval == 'latest':
            target = "cactiStyle(%s)" % target
        url = 'http://%s:%s/render?target=%s&format=json' % (
            self.host, str(self.port), target)
        try:
            time.sleep(5)
            graph_conn = urllib2.urlopen(url)
            data = graph_conn.read()
            return data
        except (ValueError, urllib2.URLError, Exception) as ex:
            LOG.error('Failed to fetch stats for metric %s of %s.Error %s ' % (
                metric_name, entity_name, str(ex)), exc_info=True)
            raise ex
        finally:
            try:
                graph_conn.close()
            except UnboundLocalError:
                pass

    def get_metrics(self, entity_name):
        url = 'http://%s:%s/metrics/index.json' % (self.host, str(self.port))
        try:
            time.sleep(5)
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
            try:
                conn.close()
            except UnboundLocalError:
                pass

    def destroy(self):
        pass
