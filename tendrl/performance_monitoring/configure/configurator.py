import ast
from etcd import EtcdConnectionFailed
from etcd import EtcdException
from etcd import EtcdKeyNotFound
import json
import logging
import multiprocessing
import signal
from tendrl.common.config import TendrlConfig
from tendrl.common.etcdobj.etcdobj import Server as etcd_server
import uuid

LOG = logging.getLogger(__name__)
config = TendrlConfig()


class Configurator(multiprocessing.Process):

    def get_configs(self, node_id=None):
        # TODO(Anmol) : Attempt reading:
        # /_tendrl/config/performance_monitoring/clusters/{cluster-id} and if
        # not already present, default back to defaults in:
        #  /_tendrl/config/performance_monitoring
        try:
            configs = ''
            if node_id is None:
                conf = self.etcd_client.read(
                    '/_tendrl/config/performance_monitoring'
                )
                configs = conf.value
            return ast.literal_eval(configs)
        except (EtcdKeyNotFound, EtcdConnectionFailed, ValueError,
                SyntaxError, EtcdException) as ex:
            LOG.error('Fetching monitoring configurations failed. Error %s' %
                      ex)
            raise ex

    def initiate_config_generation(self, conf_name, data, node_det):
        try:
            job = {
                'node_id': node_det.get('node_id'),
                "run": 'tendrl.node_monitoring.flows.configure_collectd.\
ConfigureCollectd',
                'status': 'new',
                'type': 'node',
                "parameters": {
                    'plugin_name': conf_name,
                    'plugin_conf_params': json.dumps(data),
                    'Node.fqdn': node_det['fqdn'],
                    'Service.name': 'collectd',
                },
            }
            self.etcd_client.write("/queue/%s" % uuid.uuid4(), json.dumps(job))
        except (EtcdException, EtcdConnectionFailed, EtcdException) as ex:
            LOG.error('Failed to intiate monitoring configuration for plugin \
                %s on %s with parameters %s.Error %s' % (
                conf_name, node_det['fqdn'], data, ex))
            raise ex

    def init_monitoring_on_node(self, node_det):
        # TODO(Anmol) Ideally per cluster(node's cluster) fetch config but as
        # it is defautls for now fetching only once
        configs = self.get_configs()
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

    def __init__(self, configurator_queue):
        super(Configurator, self).__init__()
        etcd_kwargs = {
            'port': int(config.get("common", "etcd_port")),
            'host': config.get("common", "etcd_connection")
        }
        self.etcd_client = etcd_server(etcd_kwargs=etcd_kwargs).client
        self._complete = multiprocessing.Event()
        self.configurator_queue = configurator_queue
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def run(self):
        try:
            while not self._complete.is_set():
                if self._complete.is_set() or self.configurator_queue._closed:
                    return
                node_det = self.configurator_queue.get()
                if node_det is not None:
                    self.init_monitoring_on_node(node_det)
        except (EtcdKeyNotFound, EtcdConnectionFailed, ValueError,
                SyntaxError, EtcdException):
            # Exception already handled by respective functions
            pass

    def stop(self):
        self._complete.set()
