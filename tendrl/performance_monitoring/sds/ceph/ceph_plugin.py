import ast

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.performance_monitoring import constants as \
    pm_consts
from tendrl.performance_monitoring.objects.system_summary \
    import SystemSummary
from tendrl.performance_monitoring.sds import SDSPlugin
from tendrl.performance_monitoring.utils import parse_resource_alerts
from tendrl.performance_monitoring.utils import read as etcd_read_key


class CephPlugin(SDSPlugin):

    name = 'ceph'

    def __init__(self):
        SDSPlugin.__init__(self)
        self.supported_services.extend([
            'tendrl-ceph-integration',
            'ceph-mon',
            'ceph-osd'
        ])
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
                config = NS.performance_monitoring.config.data['thresholds']
                if isinstance(config, basestring):
                    config = ast.literal_eval(
                        config.encode('ascii', 'ignore')
                    )
                for plugin, plugin_config in config[self.name].iteritems():
                    if isinstance(plugin_config, basestring):
                        plugin_config = ast.literal_eval(
                            plugin_config.encode('ascii', 'ignore')
                        )
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

    def get_most_used_pools(self, cluster_det):
        most_used_pools = []
        pools = cluster_det.get('Pools', {})
        p_sort = sorted(pools.keys(), key=lambda x: (pools[x]['percent_used']))
        p_sort.reverse()
        for pool_id in p_sort:
            pool_det = pools.get(pool_id)
            pool_det['cluster_name'] = cluster_det.get(
                'TendrlContext',
                {}
            ).get('sds_name', '')
            most_used_pools.append(pool_det)
        return most_used_pools[:5]

    def get_most_used_rbds(self, cluster_det):
        # Needs to be tested
        most_used_rbds = []
        pools = cluster_det.get('Pools', {})
        rbds = []
        for pool_id, pool_det in pools.iteritems():
            for rbd_id, rbd_det in pool_det.get('Rbds', {}).iteritems():
                rbd_det['percent_used'] = 0
                if rbd_det['provisioned'] != 0:
                    rbd_det['percent_used'] = (
                        int(rbd_det['used']) * 100 * 1.0
                    ) / (
                        int(rbd_det['provisioned']) * 1.0
                    )
                rbd_det['cluster_name'] = cluster_det.get(
                    'TendrlContext', {}
                ).get('sds_name', '')
                rbds.append(rbd_det)
        most_used_rbds = sorted(rbds, key=lambda k: k['percent_used'])
        most_used_rbds.reverse()
        return most_used_rbds[:5]

    def get_osd_status_wise_counts(self, cluster_det):
        osd_counts = {
            'total': 0,
            'down': 0,
            pm_consts.CRITICAL_ALERTS: 0,
            pm_consts.WARNING_ALERTS: 0
        }
        if 'maps' in cluster_det:
            osds = ast.literal_eval(
                cluster_det.get(
                    'maps', {}
                ).get(
                    'osd_map', {}
                ).get(
                    'data', {}
                ).get('osds', '[]')
            )
            for osd in osds:
                if 'up' not in osd.get('state'):
                    osd_counts['down'] = osd_counts['down'] + 1
                osd_counts['total'] = osd_counts['total'] + 1
        crit_alerts, warn_alerts = parse_resource_alerts(
            'osd',
            pm_consts.CLUSTER,
            cluster_id=cluster_det.get(
                'TendrlContext',
                {}
            ).get('integration_id', '')
        )
        osd_counts[
            pm_consts.CRITICAL_ALERTS
        ] = len(crit_alerts)
        osd_counts[
            pm_consts.WARNING_ALERTS
        ] = len(warn_alerts)
        return osd_counts

    def get_mon_status_wise_counts(self, cluster_det):
        mon_status_wise_counts = {}
        outside_quorum = ast.literal_eval(
            cluster_det.get(
                'maps', {}
            ).get(
                'mon_status', {}
            ).get(
                'data', {}
            ).get(
                'outside_quorum', '[]'
            )
        )
        mon_status_wise_counts['outside_quorum'] = len(outside_quorum)
        mon_status_wise_counts['total'] = len(
            ast.literal_eval(
                cluster_det.get(
                    'maps', {}
                ).get(
                    'mon_map', {}
                ).get(
                    'data', {}
                ).get(
                    'mons', "[]"
                )
            )
        )
        return mon_status_wise_counts

    def get_cluster_summary(self, cluster_id, cluster_det):
        ret_val = {}
        ret_val['most_used_pools'] = self.get_most_used_pools(
            cluster_det
        )
        ret_val['services_count'] = self.get_services_count(
            cluster_det
        )
        ret_val['most_used_rbds'] = self.get_most_used_rbds(
            cluster_det
        )
        ret_val['osd_counts'] = self.get_osd_status_wise_counts(
            cluster_det
        )
        ret_val['mon_counts'] = self.get_mon_status_wise_counts(cluster_det)
        return ret_val

    def get_system_mon_status_wise_counts(self, cluster_summaries):
        mon_status_wise_counts = {}
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_mon_count = \
                    cluster_summary.sds_det.get('mon_counts', {})
                if (
                    isinstance(cluster_mon_count, unicode) and not
                        isinstance(cluster_mon_count, dict)
                ):
                    cluster_mon_count = ast.literal_eval(
                        cluster_mon_count.encode('ascii', 'ignore')
                    )
                for status, count in cluster_mon_count.iteritems():
                    mon_status_wise_counts[status] = \
                        mon_status_wise_counts.get(status, 0) + int(count)
        return mon_status_wise_counts

    def get_system_osd_status_wise_counts(self, cluster_summaries):
        osd_status_wise_counts = {}
        osd_critical_alerts = 0
        osd_warning_alerts = 0
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_osd_count = \
                    cluster_summary.sds_det.get('osd_counts', {})
                if (
                    isinstance(cluster_osd_count, unicode) and not
                        isinstance(cluster_osd_count, dict)
                ):
                    cluster_osd_count = ast.literal_eval(
                        cluster_osd_count.encode('ascii', 'ignore')
                    )
                for status, count in cluster_osd_count.iteritems():
                    if isinstance(count, int):
                        osd_status_wise_counts[status] = \
                            osd_status_wise_counts.get(status, 0) + count
                osd_critical_alerts = \
                    osd_critical_alerts + cluster_osd_count.get(
                        pm_consts.CRITICAL_ALERTS
                    )
                osd_warning_alerts = \
                    osd_warning_alerts + cluster_osd_count.get(
                        pm_consts.WARNING_ALERTS
                    )
        osd_status_wise_counts[pm_consts.WARNING_ALERTS] = \
            osd_warning_alerts
        osd_status_wise_counts[pm_consts.CRITICAL_ALERTS] = \
            osd_critical_alerts
        return osd_status_wise_counts

    def get_system_max_used_pools(self, cluster_summaries):
        pools = []
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_most_used_pools = \
                    cluster_summary.sds_det.get('most_used_pools', {})
                if isinstance(cluster_most_used_pools, basestring):
                    cluster_most_used_pools = ast.literal_eval(
                        cluster_most_used_pools.encode('ascii', 'ignore')
                    )
                for pool in cluster_most_used_pools:
                    if isinstance(pool, unicode):
                        pool = pool.encode('ascii', 'ignore')
                        pool = ast.literal_eval(pool)
                    pools.append(pool)
        most_used_pools = \
            sorted(pools, key=lambda k: k['percent_used'])
        most_used_pools.reverse()
        return most_used_pools[:5]

    def get_system_max_used_rbds(self, cluster_summaries):
        rbds = []
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_most_used_rbds = \
                    cluster_summary.sds_det.get('most_used_rbds', {})
                if (
                    isinstance(cluster_most_used_rbds, unicode) and not
                        isinstance(cluster_most_used_rbds, list)
                ):
                    cluster_most_used_rbds = ast.literal_eval(
                        cluster_most_used_rbds.encode('ascii', 'ignore')
                    )
                rbds.extend(cluster_most_used_rbds)
        most_used_rbds = \
            sorted(rbds, key=lambda k: k['percent_used'])
        most_used_rbds.reverse()
        return most_used_rbds[:5]

    def compute_system_summary(self, cluster_summaries, clusters):
        try:
            SystemSummary(
                utilization=self.get_system_utilization(cluster_summaries),
                hosts_count=self.get_system_host_status_wise_counts(
                    cluster_summaries
                ),
                cluster_count=self.get_clusters_status_wise_counts(clusters),
                sds_det={
                    'mon_counts': self.get_system_mon_status_wise_counts(
                        cluster_summaries
                    ),
                    'osd_counts': self.get_system_osd_status_wise_counts(
                        cluster_summaries
                    ),
                    'most_used_pools': self.get_system_max_used_pools(
                        cluster_summaries
                    ),
                    'most_used_rbds': self.get_system_max_used_rbds(
                        cluster_summaries
                    )
                },
                sds_type=self.name
            ).save(update=False)
        except Exception as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": "Exception caught computing system "
                                        "summary.",
                             "exception": ex
                             }
                )
            )
