from etcd import EtcdConnectionFailed
from etcd import EtcdException
from etcd import EtcdKeyNotFound
import logging
from tendrl.commons import central_store
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.objects.summary \
    import PerformanceMonitoringSummary
import yaml


LOG = logging.getLogger(__name__)


class PerformanceMonitoringEtcdCentralStore(central_store.EtcdCentralStore):
    def __init__(self):
        super(PerformanceMonitoringEtcdCentralStore, self).__init__()

    def save_config(self, config):
        tendrl_ns.etcd_orm.save(config)

    def save_definition(self, definition):
        tendrl_ns.etcd_orm.save(definition)

    def get_configs(self):
        # TODO(Anmol) : Attempt reading:
        # /_tendrl/config/performance_monitoring/clusters/{cluster-id} and if
        # not already present, default back to defaults in:
        #  /_tendrl/config/performance_monitoring
        try:
            configs = ''
            conf = tendrl_ns.etcd_orm.client.read(
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
            node_name_path = '/nodes/%s/NodeContext/fqdn' % node_id
            return tendrl_ns.etcd_orm.client.read(node_name_path).value
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
            nodes_etcd = tendrl_ns.etcd_orm.client.read('/nodes')
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
        # Logic to be implemented once alerting module is functional
        return alerts_arr

    def get_node_summary(self, node_ids=None):
        try:
            summary = []
            if node_ids is None:
                node_ids = self.get_node_ids()
            for node_id in node_ids:
                current_node_summary = PerformanceMonitoringSummary(
                    node_id,
                    cpu_usage={
                        'percent_used': '',
                        'updated_at': ''
                    },
                    memory_usage={
                        'percent_used': '',
                        'updated_at': '',
                        'used': '',
                        'total': ''
                    },
                    storage_usage={
                        'percent_used': '',
                        'total': '',
                        'used': '',
                        'updated_at': ''
                    },
                    alert_count=0
                ).load().to_json()
                del current_node_summary['_etcd_cls']
                del current_node_summary['value']
                del current_node_summary['attrs']
                del current_node_summary['obj_list']
                del current_node_summary['enabled']
                del current_node_summary['obj_value']
                del current_node_summary['flows']
                del current_node_summary['atoms']
                summary.append(current_node_summary)
            return summary
        except EtcdKeyNotFound as ex:
            raise TendrlPerformanceMonitoringException(str(ex))
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
            nodes = tendrl_ns.etcd_orm.client.read('/nodes/', recursive=True)
            for node in nodes._children:
                if node['key'].startswith('/nodes/'):
                    node_id = (
                        node['key'][len('/nodes/'):]
                    ).encode('ascii', 'ignore')
                    fqdn = (
                        tendrl_ns.etcd_orm.client.read(
                            '%s/NodeContext/fqdn' % (node['key']),
                            recursive=True
                        ).value
                    ).encode('ascii', 'ignore')
                    nodes_dets.append({'node_id': node_id, 'fqdn': fqdn})
            return nodes_dets
        except EtcdKeyNotFound:
            return nodes_dets
        except EtcdConnectionFailed as ex:
            raise TendrlPerformanceMonitoringException(str(ex))

    def save_performancemonitoringsummary(self, node_summary):
        tendrl_ns.etcd_orm.save(node_summary)
