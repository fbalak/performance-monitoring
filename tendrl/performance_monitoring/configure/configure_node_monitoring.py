import ast
from etcd import EtcdConnectionFailed
import gevent.event
import gevent.greenlet

from tendrl.commons import etcdobj
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
            etcd_kwargs = {
                'port': int(
                    NS.performance_monitoring.config.data['etcd_port']),
                'host': NS.performance_monitoring.config.data[
                    "etcd_connection"]
            }
            self.etcd_orm = etcdobj.Server(etcd_kwargs=etcd_kwargs)
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
            self.init_monitoring()
            self._complete = gevent.event.Event()
        except TendrlPerformanceMonitoringException as ex:
            raise ex

    def _run(self):
        try:
            while not self._complete.is_set():
                gevent.sleep(1)
                node_changes = self.etcd_orm.client.watch(
                    '/nodes', recursive=True, timeout=0)
                if node_changes is not None and node_changes.value is not None:
                    node_id = node_changes.key
                    if node_changes.key.startswith('/nodes/') \
                            and node_changes.key.endswith(
                                '/NodeContext/fqdn'):
                        nodeid_pre_trim = node_id[len('/nodes/'):]
                        node_id = nodeid_pre_trim[: -len('/NodeContext/fqdn')]
                        fqdn = node_changes.value
                        if node_id not in self.monitoring_config_init_nodes:
                            gevent.sleep(0.1)
                            gevent.spawn(
                                self.init_monitoring_on_node,
                                {
                                    'node_id': node_id,
                                    'fqdn': fqdn
                                }
                            )
                            self.monitoring_config_init_nodes.append(node_id)
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
