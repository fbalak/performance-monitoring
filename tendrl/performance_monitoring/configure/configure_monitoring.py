from etcd import EtcdConnectionFailed
import logging
import multiprocessing
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException


LOG = logging.getLogger(__name__)


class ConfigureMonitoring(multiprocessing.Process):
    def watch_nodes(self):
        try:
            while True:
                node_changes = self.persister.get_store().client.watch(
                    '/nodes', recursive=True, timeout=0)
                if node_changes is not None and node_changes.value is not None:
                    node_id = node_changes.key
                    if node_changes.key.startswith('/nodes/') \
                            and node_changes.key.endswith(
                                '/Node_context/fqdn'):
                        nodeid_pre_trim = node_id[len('/nodes/'):]
                        node_id = nodeid_pre_trim[: -len('/Node_context/fqdn')]
                        fqdn = node_changes.value
                        self.configurator_queue.put(
                            {'node_id': node_id, 'fqdn': fqdn}
                        )
        except EtcdConnectionFailed as e:
            LOG.error(
                'Exception %s caught while watching alerts' % str(e),
                exc_info=True
            )

    def init_monitoring(self):
        try:
            node_dets = self.persister.get_nodes_details()
            for node_det in node_dets:
                self.configurator_queue.put(node_det)
        except TendrlPerformanceMonitoringException as ex:
            LOG.error(
                'Failed to intialize monitoring configuration on nodes. '
                'Error %s' % str(ex),
                exc_info=True
            )
            raise ex

    def __init__(self, configurator_queue, persister_instance):
        try:
            super(ConfigureMonitoring, self).__init__()
            self.persister = persister_instance
            self.configurator_queue = configurator_queue
            self.init_monitoring()
        except TendrlPerformanceMonitoringException as ex:
            raise ex

    def run(self):
        self.watch_nodes()
