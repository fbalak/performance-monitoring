from etcd import EtcdConnectionFailed
import logging
import multiprocessing
from tendrl.commons import etcdobj
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException


LOG = logging.getLogger(__name__)


class ConfigureMonitoring(multiprocessing.Process):
    def watch_nodes(self):
        etcd_kwargs = {
            'port': tendrl_ns.config.data['etcd_port'],
            'host': tendrl_ns.config.data["etcd_connection"]
        }
        etcd_orm = etcdobj.Server(etcd_kwargs=etcd_kwargs)
        try:
            while True:
                node_changes = etcd_orm.client.watch(
                    '/nodes', recursive=True, timeout=0)
                if node_changes is not None and node_changes.value is not None:
                    node_id = node_changes.key
                    if node_changes.key.startswith('/nodes/') \
                            and node_changes.key.endswith(
                                '/NodeContext/fqdn'):
                        nodeid_pre_trim = node_id[len('/nodes/'):]
                        node_id = nodeid_pre_trim[: -len('/NodeContext/fqdn')]
                        fqdn = node_changes.value
                        if node_id not in tendrl_ns.monitoring_config_init_nodes:
                            tendrl_ns.configurator_queue.put(
                                {'node_id': node_id, 'fqdn': fqdn}
                            )
                            tendrl_ns.monitoring_config_init_nodes.append(node_id)
        except EtcdConnectionFailed as e:
            LOG.error(
                'Exception %s caught while watching alerts' % str(e),
                exc_info=True
            )

    def init_monitoring(self):
        try:
            node_dets = tendrl_ns.central_store_thread.get_nodes_details()
            for node_det in node_dets:
                if (
                    node_det['node_id'] not in
                    tendrl_ns.monitoring_config_init_nodes
                ):
                    tendrl_ns.configurator_queue.put(node_det)
                    tendrl_ns.monitoring_config_init_nodes.append(node_det['node_id'])
        except TendrlPerformanceMonitoringException as ex:
            LOG.error(
                'Failed to intialize monitoring configuration on nodes. '
                'Error %s' % str(ex),
                exc_info=True
            )
            raise ex

    def __init__(self):
        try:
            super(ConfigureMonitoring, self).__init__()
            self.init_monitoring()
        except TendrlPerformanceMonitoringException as ex:
            raise ex

    def run(self):
        self.watch_nodes()
