from etcd import EtcdConnectionFailed
from etcd import EtcdException
import json
import logging
import multiprocessing
import signal
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
import time
import uuid

LOG = logging.getLogger(__name__)


class Configurator(multiprocessing.Process):

    # This is a temporary fix only retained till the issue with multiprocessing
    # queue semaphore issue is fixed instead of the current workaround
    configured_nodes = []

    def initiate_config_generation(self, conf_name, data, node_det):
        try:
            job = {
                'node_ids': [node_det.get('node_id')],
                "run": 'tendrl.node_monitoring.flows.configure_collectd.ConfigureCollectd',
                'status': 'new',
                'type': 'monitoring',
                'integration_id': tendrl_ns.tendrl_context.integration_id,
                "parameters": {
                    'plugin_name': conf_name,
                    'plugin_conf_params': json.dumps(data),
                    'Node.fqdn': node_det['fqdn'],
                    'Service.name': 'collectd',
                },
            }
            tendrl_ns.etcd_orm.client.write(
                "/queue/%s" % str(uuid.uuid4()),
                json.dumps(job)
            )
        except (EtcdException, EtcdConnectionFailed, EtcdException) as ex:
            LOG.error('Failed to intiate monitoring configuration for plugin \
                %s on %s with parameters %s.Error %s' % (
                conf_name, node_det['fqdn'], data, ex))
            raise TendrlPerformanceMonitoringException(str(ex))

    def init_monitoring_on_node(self, node_det):
        # TODO(Anmol) Ideally per cluster(node's cluster) fetch config but as
        # it is defautls for now fetching only once
        configs = tendrl_ns.config.data
        global_configs = {}
        global_configs['master_name'] = configs['master_name']
        global_configs['interval'] = configs['interval']
        data = {}
        data.update(global_configs)
        self.initiate_config_generation('collectd', data, node_det)
        self.initiate_config_generation('dbpush', data, node_det)
        for plugin, plugin_config in configs['thresholds'].iteritems():
            data.update(plugin_config)
            self.initiate_config_generation(plugin, data, node_det)

    def __init__(self):
        super(Configurator, self).__init__()
        self._complete = multiprocessing.Event()
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def run(self):
        try:
            while not self._complete.is_set():
                if self._complete.is_set() or tendrl_ns.configurator_queue._closed:
                    return
                tendrl_ns.configurator_queue._sem.acquire(True, None)
                node_det = tendrl_ns.configurator_queue.get()
                if (
                    node_det is not None and
                    node_det['node_id'] not in self.configured_nodes
                ):
                    time.sleep(10)
                    self.init_monitoring_on_node(node_det)
                    self.configured_nodes.append(node_det['node_id'])
        except TendrlPerformanceMonitoringException:
            # Exception already handled by respective functions
            pass

    def stop(self):
        self._complete.set()
