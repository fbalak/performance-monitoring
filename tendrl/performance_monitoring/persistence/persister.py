import ast
from etcd import EtcdConnectionFailed
from etcd import EtcdException
from etcd import EtcdKeyNotFound
import logging
from tendrl.commons.persistence.etcd_persister import EtcdPersister
from tendrl.performance_monitoring.manager.\
    tendrl_definitions_performance_monitoring import data as def_data
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.persistence.tendrl_definitions \
    import TendrlDefinitions
import time
import yaml


LOG = logging.getLogger(__name__)


class PerformanceMonitoringEtcdPersister(EtcdPersister):
    def __init__(self, config):
        # Since this is a singleton class the singleton framework ensures only
        # a single call to this constructor in the life time of the application
        # However wherever the class is attempted to be intialized, it tries to
        # match the constructor and hence the 2nd arguement is made to appear
        # as an optional arguement although it is enforced internally not be
        # optional due to reason stated above.
        if config is not None:
            super(PerformanceMonitoringEtcdPersister, self).__init__(config)
            self._store = self.get_store()
        else:
            raise ValueError(
                'Failed to create persister.Error: config not intialised'
            )

    def update_defs(self):
        defs_path = 'tendrl_definitions_node-agent/data'
        try:
            defs = yaml.load(self._store.client.read(
                defs_path).value.decode("utf-8"))
            perf_defs = yaml.load(def_data)
            for key in perf_defs:
                if key.startswith('namespace.'):
                    namespace = key
            defs[namespace] = perf_defs[namespace]
            self._store.save(
                TendrlDefinitions(
                    updated=str(time.time()),
                    data=yaml.safe_dump(defs)
                )
            )
        except EtcdKeyNotFound:
            try:
                self._store.save(
                    TendrlDefinitions(
                        updated=str(time.time()),
                        data=def_data
                    )
                )
            except (
                EtcdConnectionFailed,
                ValueError,
                SyntaxError,
                EtcdException,
                TypeError
            ) as ex:
                raise TendrlPerformanceMonitoringException(str(ex))

    def get_configs(self):
        # TODO(Anmol) : Attempt reading:
        # /_tendrl/config/performance_monitoring/clusters/{cluster-id} and if
        # not already present, default back to defaults in:
        #  /_tendrl/config/performance_monitoring
        try:
            configs = ''
            conf = self._store.client.read(
                '/_tendrl/config/performance_monitoring'
            )
            configs = conf.value
            return yaml.safe_load(configs)
        except (EtcdKeyNotFound, EtcdConnectionFailed, ValueError,
                SyntaxError, EtcdException) as ex:
            LOG.error('Fetching monitoring configurations failed. Error %s' %
                      ex)
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_node_name_from_id(self, node_id):
        try:
            node_name_path = '/nodes/%s/Node_context/fqdn' % node_id
            return self._store.client.read(node_name_path).value
        except (
            EtcdKeyNotFound,
            EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            EtcdException,
            TypeError
        ) as ex:
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_node_ids(self):
        try:
            node_ids = []
            nodes_etcd = self._store.client.read('/nodes')
            for node in nodes_etcd._children:
                node_ids.append(node['key'][len('/nodes/'):])
            return node_ids
        except EtcdKeyNotFound:
            return []
        except (
            EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            TypeError
        ) as ex:
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_alerts(self, node_ids=None):
        alerts_arr = []
        try:
            alerts = self._store.client.read('/alerts', recursive=True)
        except EtcdKeyNotFound:
            return alerts_arr
        except (
            EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            TypeError
        ) as ex:
            raise TendrlPerformanceMonitoringException(str(ex))
        for child in alerts._children:
            alert = yaml.safe_load(child['value'])
            if node_ids is not None:
                if alert['node_id'] in node_ids:
                    alerts_arr.append(alert)
            else:
                alerts_arr.append(alert)
        return alerts_arr

    def get_node_summary(self, node_ids=None):
        try:
            if isinstance(node_ids, str):
                return ast.literal_eval(
                    self._store.client.read(
                        '/monitoring/summary/%s' % node_ids
                    ).value
                )
            if node_ids is None or isinstance(node_ids, list):
                ret_val = []
                monitoring_node_det = self._store.client.read(
                    '/monitoring/summary/',
                    recursive=True
                )
                for child in monitoring_node_det._children:
                    if 'summary' in child['key']:
                        node_summary = {
                            'node_id': (
                                child['key'][len('/monitoring/summary/'):]
                            ).encode('ascii', 'ignore'),
                            'summary': yaml.safe_load(child['value'])
                        }
                        if node_ids is not None:
                            if node_summary['node_id'] in node_ids:
                                ret_val.append(node_summary)
                        else:
                            ret_val.append(node_summary)
                return ret_val
        except EtcdKeyNotFound:
            return None
        except (
            EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            TypeError
        ) as ex:
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_nodes_details(self):
        nodes_dets = []
        try:
            nodes = self._store.client.read('/nodes/', recursive=True)
            for node in nodes._children:
                if node['key'].startswith('/nodes/'):
                    node_id = (
                        node['key'][len('/nodes/'):]
                    ).encode('ascii', 'ignore')
                    fqdn = (
                        self._store.client.read(
                            '%s/Node_context/fqdn' % (node['key']),
                            recursive=True
                        ).value
                    ).encode('ascii', 'ignore')
                    nodes_dets.append({'node_id': node_id, 'fqdn': fqdn})
            return nodes_dets
        except EtcdKeyNotFound:
            return nodes_dets
        except EtcdConnectionFailed as ex:
            raise TendrlPerformanceMonitoringException(str(ex))

    def save_node_summary(self, summary, node_id):
        try:
            self._store.client.write(
                '/monitoring/summary/%s' % node_id,
                yaml.safe_dump(summary)
            )
        except (
            EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            TypeError
        ) as ex:
            raise TendrlPerformanceMonitoringException(str(ex))
