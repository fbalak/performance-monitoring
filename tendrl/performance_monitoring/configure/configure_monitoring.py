from etcd import EtcdConnectionFailed
from etcd import EtcdKeyNotFound
import logging
import multiprocessing
from tendrl.common.config import TendrlConfig
from tendrl.common.etcdobj.etcdobj import Server as etcd_server


config = TendrlConfig()


LOG = logging.getLogger(__name__)


class ConfigureMonitoring(multiprocessing.Process):

    def get_nodes_details(self):
        nodes_dets = []
        try:
            nodes = self.etcd_client.read('/nodes/', recursive=True)
            for node in nodes._children:
                if node['key'].startswith('/nodes/'):
                    node_id = node['key'][len('/nodes/'):]
                    fqdn = self.etcd_client.read(
                        '%s/Node_context/fqdn' %
                        (node['key']), recursive=True).value
                    nodes_dets.append({'node_id': node_id, 'fqdn': fqdn})
            return nodes_dets
        except (EtcdConnectionFailed, EtcdKeyNotFound):
            return nodes_dets

    def watch_nodes(self):
        try:
            while True:
                node_changes = self.etcd_client.watch(
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
        node_dets = self.get_nodes_details()
        for node_det in node_dets:
            self.configurator_queue.put(node_det)

    def __init__(self, configurator_queue):
        super(ConfigureMonitoring, self).__init__()
        etcd_kwargs = {
            'port': int(config.get("common", "etcd_port")),
            'host': config.get("common", "etcd_connection")
        }
        self.etcd_client = etcd_server(etcd_kwargs=etcd_kwargs).client
        self.configurator_queue = configurator_queue
        self.init_monitoring()

    def run(self):
        self.watch_nodes()

    def stop(self):
        pass
