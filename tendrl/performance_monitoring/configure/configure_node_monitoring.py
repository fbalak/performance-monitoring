import ast
from etcd import EtcdConnectionFailed
import gevent.event
import gevent.greenlet

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.utils import initiate_config_generation


class ConfigureNodeMonitoring(gevent.greenlet.Greenlet):
    def init_monitoring(self):
        try:
            node_dets = NS.central_store_thread.get_nodes_details()
            for node_det in node_dets:
                if (
                    node_det['node_id'] not in
                    self.monitoring_config_init_nodes
                ):
                    self.init_monitoring_on_node(node_det)
                    self.monitoring_config_init_nodes.append(
                        node_det['node_id']
                    )
        except TendrlPerformanceMonitoringException as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": 'Failed to intialize monitoring '
                                        'configuration on nodes. ',
                             "exception": ex
                             }
                )
            )
            raise ex

    def init_monitoring_on_node(self, node_det):
        # TODO(Anmol) Ideally per cluster(node's cluster) fetch config but as
        # it is defautls for now fetching only once
        gevent.sleep(0.1)
        initiate_config_generation(
            {
                'node_id': node_det['node_id'],
                'fqdn': node_det['fqdn'],
                'plugin': 'collectd',
                'plugin_conf': {
                    'master_name': NS.performance_monitoring.config.data[
                        'master_name'],
                    'interval': NS.performance_monitoring.config.data[
                        'interval']
                }
            }
        )
        gevent.sleep(0.1)
        initiate_config_generation(
            {
                'node_id': node_det['node_id'],
                'fqdn': node_det['fqdn'],
                'plugin': 'dbpush',
                'plugin_conf': {
                    'master_name': NS.performance_monitoring.config.data[
                        'master_name'],
                    'interval': NS.performance_monitoring.config.data[
                        'interval']
                }
            }
        )
        initiate_config_generation(
            {
                'node_id': node_det['node_id'],
                'fqdn': node_det['fqdn'],
                'plugin': 'latency',
                'plugin_conf': {
                    'master_name': NS.performance_monitoring.config.data[
                        'master_name'],
                    'interval': NS.performance_monitoring.config.data[
                        'interval']
                }
            }
        )
        config = NS.performance_monitoring.config.data['thresholds']
        if isinstance(config, basestring):
            config = ast.literal_eval(config.encode('ascii', 'ignore'))
        for plugin, plugin_config in config['node'].iteritems():
            if isinstance(plugin_config, basestring):
                plugin_config = ast.literal_eval(
                    plugin_config.encode('ascii', 'ignore')
                )
            gevent.sleep(0.1)
            initiate_config_generation(
                {
                    'node_id': node_det['node_id'],
                    'fqdn': node_det['fqdn'],
                    'plugin': plugin,
                    'plugin_conf': plugin_config
                }
            )

    def __init__(self):
        super(ConfigureNodeMonitoring, self).__init__()
        try:
            self.monitoring_config_init_nodes = []
            self._complete = gevent.event.Event()
        except TendrlPerformanceMonitoringException as ex:
            raise ex

    def _run(self):
        try:
            while not self._complete.is_set():
                gevent.sleep(0.1)
                self.init_monitoring()
                gevent.sleep(10)
        except (EtcdConnectionFailed, Exception) as e:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": 'Exception caught while watching '
                                        'alerts',
                             "exception": e
                             }
                )
            )

    def stop(self):
        self._complete.set()
