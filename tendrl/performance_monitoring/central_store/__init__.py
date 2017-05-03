from etcd import EtcdConnectionFailed
from etcd import EtcdException
from etcd import EtcdKeyNotFound
from ruamel import yaml

from tendrl.commons import central_store
from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.objects.cluster_summary \
    import ClusterSummary
from tendrl.performance_monitoring.objects.node_summary \
    import NodeSummary
from tendrl.performance_monitoring.objects.system_summary \
    import SystemSummary
from tendrl.performance_monitoring.utils import read as etcd_read


class PerformanceMonitoringEtcdCentralStore(central_store.EtcdCentralStore):
    def __init__(self):
        super(PerformanceMonitoringEtcdCentralStore, self).__init__()

    def save_config(self, config):
        NS.etcd_orm.save(config)

    def save_definition(self, definition):
        NS.etcd_orm.save(definition)

    def get_configs(self):
        # TODO(Anmol) : Attempt reading:
        # /_tendrl/config/performance_monitoring/clusters/{cluster-id} and if
        # not already present, default back to defaults in:
        #  /_tendrl/config/performance_monitoring
        try:
            configs = ''
            conf = NS.etcd_orm.client.read(
                '_NS/performance_monitoring/config'
            )
            configs = conf.value
            return yaml.safe_load(configs)
        except (EtcdKeyNotFound, EtcdConnectionFailed, ValueError,
                SyntaxError, EtcdException) as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": 'Fetching monitoring configurations '
                                        'failed.',
                             "exception": ex
                             }
                )
            )
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_node_last_seen_at(self, node_id):
        try:
            return NS.etcd_orm.client.read(
                '/monitoring/nodes/%s/last_seen_at' % node_id
            ).value
        except Exception:
            return None

    def get_node_name_from_id(self, node_id):
        try:
            node_name_path = '/nodes/%s/NodeContext/fqdn' % node_id
            return NS.etcd_orm.client.read(node_name_path).value
        except (
            EtcdKeyNotFound,
            EtcdConnectionFailed,
            ValueError,
            SyntaxError,
            EtcdException,
            TypeError
        ) as ex:
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_node_role(self, node_id):
        try:
            return NS.etcd_orm.client.read(
                '/nodes/%s/NodeContext/tags' % node_id
            ).value
        except Exception as ex:
            raise TendrlPerformanceMonitoringException(
                "Failed to fetch the role of node %s. Error %s" % (
                    node_id,
                    str(ex)
                )
            )

    def get_node_cluster_name(self, node_id):
        try:
            return NS.etcd_orm.client.read(
                '/nodes/%s/TendrlContext/cluster_name' % node_id
            ).value
        except Exception as ex:
            raise TendrlPerformanceMonitoringException(
                "Failed to fetch cluster name for node %s. Error: %s" % (
                    node_id,
                    str(ex)
                )
            )

    def get_node_ids(self):
        try:
            node_ids = []
            nodes_etcd = NS.etcd_orm.client.read('/nodes')
            for node in nodes_etcd.leaves:
                node_key_contents = node.key.split('/')
                if len(node_key_contents) == 3:
                    node_ids.append(node_key_contents[2])
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

    def get_node_alert_ids(self, node_id=None):
        alert_ids = []
        try:
            alerts = NS.etcd_orm.client.read(
                '/alerting/nodes/%s' % node_id
            )
            for alert in alerts.leaves:
                key_contents = alert.key.split('/')
                if len(key_contents) == 5:
                    alert_ids.append(
                        key_contents[4]
                    )
        except EtcdKeyNotFound as ex:
            return alert_ids
        except (
            EtcdConnectionFailed,
            EtcdException
        ) as ex:
            raise TendrlPerformanceMonitoringException(str(ex))
        return alert_ids

    def get_node_alerts(self, node_id):
        alert_root = '/alerting/nodes/%s' % node_id
        node_alerts = etcd_read(alert_root)
        node_alerts_arr = []
        for alert_id, node_alert in node_alerts.iteritems():
            node_alerts_arr.append(node_alert)
        return node_alerts_arr

    def get_cluster_alerts(self, cluster_id):
        cluster_alerts = []
        try:
            c_alerts = etcd_read(
                '/alerting/clusters/%s' % cluster_id
            )
            for alert_id, alert in c_alerts.iteritems():
                cluster_alerts.append(alert)
            return cluster_alerts
        except Exception:
            return cluster_alerts

    def get_cluster_summary(self, cluster_id):
        try:
            summary = ClusterSummary(
                cluster_id=cluster_id
            )
            if not summary.exists():
                raise TendrlPerformanceMonitoringException(
                    "No summary found for cluster %s" % cluster_id
                )
            summary = summary.load().to_json()
            if '_etcd_cls' in summary:
                    del summary['_etcd_cls']
            if 'value' in summary:
                del summary['value']
            if '_defs' in summary:
                del summary['_defs']
            if 'list' in summary:
                del summary['list']
            return summary
        except Exception as ex:
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_system_summary(self, cluster_type):
        try:
            summary = SystemSummary(
                sds_type=cluster_type
            )
            if not summary.exists():
                raise TendrlPerformanceMonitoringException(
                    "No clusters of type %s found" % cluster_type
                )
            summary = summary.load().to_json()
            if '_etcd_cls' in summary:
                    del summary['_etcd_cls']
            if 'value' in summary:
                del summary['value']
            if '_defs' in summary:
                del summary['_defs']
            if 'list' in summary:
                del summary['list']
            return summary
        except Exception as ex:
            raise TendrlPerformanceMonitoringException(str(ex))

    def get_node_summary(self, node_ids=None):
        summary = []
        exs = ''
        if node_ids is None:
            node_ids = self.get_node_ids()
        for node_id in node_ids:
            try:
                current_node_summary = etcd_read(
                    '/monitoring/summary/nodes/%s' % node_id
                )
                if '_etcd_cls' in current_node_summary:
                    del current_node_summary['_etcd_cls']
                if 'value' in current_node_summary:
                    del current_node_summary['value']
                if '_defs' in current_node_summary:
                    del current_node_summary['_defs']
                if 'list' in current_node_summary:
                    del current_node_summary['list']
                summary.append(current_node_summary)
            except EtcdKeyNotFound:
                exs = "%s.Failed to fetch summary for node with id: %s" % (
                    exs,
                    node_id
                )
                continue
        if len(summary) == len(node_ids):
            return summary, 200, None
        else:
            if len(summary) == 0:
                return summary, 500, exs
            else:
                return summary, 206, exs

    def get_nodes_details(self):
        nodes_dets = []
        try:
            nodes = NS.etcd_orm.client.read('/nodes/')
            for node in nodes.leaves:
                if node.key.startswith('/nodes/'):
                    node_id = (
                        node.key.split('/')[2]
                    ).encode('ascii', 'ignore')
                    fqdn = (
                        NS.etcd_orm.client.read(
                            '/nodes/%s/NodeContext/fqdn' % (node_id)
                        ).value
                    ).encode('ascii', 'ignore')
                    nodes_dets.append({'node_id': node_id, 'fqdn': fqdn})
            return nodes_dets
        except EtcdKeyNotFound:
            return nodes_dets
        except EtcdConnectionFailed as ex:
            raise TendrlPerformanceMonitoringException(str(ex))

    def save_nodesummary(self, node_summary):
        NS.etcd_orm.save(node_summary)

    def get_cluster_node_ids(self, cluster_id):
        cluster_nodes = []
        try:
            nodes = NS.etcd_orm.client.read(
                '/clusters/%s/nodes' % cluster_id
            )
            for node in nodes.leaves:
                key_contents = node.key.split('/')
                if len(key_contents) == 5:
                    cluster_nodes.append(key_contents[4])
            return cluster_nodes
        except EtcdKeyNotFound:
            return cluster_nodes

    def save_clustersummary(self, cluster_summary):
        NS.etcd_orm.save(cluster_summary)

    def save_systemsummary(self, system_summary):
        NS.etcd_orm.save(system_summary)

    def get_node_names_in_cluster(self, cluster_id):
        ret_val = []
        nodes = etcd_read('/clusters/%s/nodes' % cluster_id)
        for node_id, node_det in nodes.iteritems():
            ret_val.append(node_det.get('NodeContext', {}).get('fqdn'))
        return ret_val
