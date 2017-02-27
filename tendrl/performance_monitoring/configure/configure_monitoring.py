from etcd import EtcdConnectionFailed
import gevent.event
import gevent.greenlet
import logging
from tendrl.commons import etcdobj
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException


LOG = logging.getLogger(__name__)


class ConfigureMonitoring(gevent.greenlet.Greenlet):
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
            etcd_kwargs = {
                'port': tendrl_ns.config.data['etcd_port'],
                'host': tendrl_ns.config.data["etcd_connection"]
            }
            self.etcd_orm = etcdobj.Server(etcd_kwargs=etcd_kwargs)
        except TendrlPerformanceMonitoringException as ex:
            LOG.error(
                'Failed to intialize monitoring configuration on nodes. '
                'Error %s' % str(ex),
                exc_info=True
            )
            raise ex

    def __init__(self):
        super(ConfigureMonitoring, self).__init__()
        try:
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

    def stop(self):
        self._complete.set()
