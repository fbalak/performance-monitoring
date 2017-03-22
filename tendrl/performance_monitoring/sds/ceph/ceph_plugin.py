from tendrl.commons.utils.etcd_util import read as etcd_read_key
from tendrl.performance_monitoring.sds import SDSPlugin
import logging


LOG = logging.getLogger(__name__)


class CephPlugin(SDSPlugin):

    name = 'ceph'

    def __init__(self):
        SDSPlugin.__init__(self)
        self.configured_nodes = {}

    def configure_monitoring(self, sds_tendrl_context):
        configs = []
        cluster_node_ids = \
            NS.central_store_thread.get_cluster_node_ids(
                sds_tendrl_context['integration_id']
            )
        for node_id in cluster_node_ids:
            sds_node_context = etcd_read_key(
                '/clusters/%s/nodes/%s/NodeContext' % (
                    sds_tendrl_context['integration_id'],
                    node_id
                )
            )
            if 'mon' in sds_node_context['tags']:
                for plugin, plugin_config in \
                        NS.performance_monitoring.config.data[
                            'thresholds'
                        ][
                            self.name
                        ].iteritems():
                    is_configured = True
                    if node_id not in self.configured_nodes:
                        self.configured_nodes[node_id] = [plugin]
                        is_configured = False
                    if plugin not in self.configured_nodes[node_id]:
                        node_plugins = self.configured_nodes[node_id]
                        node_plugins.append(plugin)
                        is_configured = False
                    if not is_configured:
                        plugin_config['cluster_id'] = \
                            sds_tendrl_context['integration_id']
                        configs.append({
                            'plugin': "%s_%s" % (self.name, plugin),
                            'plugin_conf': plugin_config,
                            'node_id': node_id,
                            'fqdn': sds_node_context['fqdn']
                        })
        return configs
