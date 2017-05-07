import ast
from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.performance_monitoring import constants as \
    pm_consts
from tendrl.performance_monitoring.objects.system_summary \
    import SystemSummary
from tendrl.performance_monitoring.sds import SDSPlugin
from tendrl.performance_monitoring.sds.ceph.pg_utils \
    import _calculate_pg_counters
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
                    if plugin not in self.configured_nodes.get(node_id, []):
                        node_plugins = self.configured_nodes.get(node_id, [])
                        node_plugins.append(plugin)
                        is_configured = False
                    if not is_configured:
                        plugin_config['cluster_id'] = \
                            sds_tendrl_context['integration_id']
                        plugin_config['cluster_name'] = \
                            sds_tendrl_context['cluster_name']
                        configs.append({
                            'plugin': "%s_%s" % (self.name, plugin),
                            'plugin_conf': plugin_config,
                            'node_id': node_id,
                            'fqdn': sds_node_context['fqdn']
                        })
                is_configured = True
                if (
                    "ceph_cluster_iops" not in
                        self.configured_nodes.get(node_id, [])
                ):
                    node_plugins = self.configured_nodes.get(node_id, [])
                    node_plugins.append(
                        "ceph_cluster_iops"
                    )
                    is_configured = False
                if not is_configured:
                    plugin_config['cluster_id'] = \
                        sds_tendrl_context['integration_id']
                    plugin_config['cluster_name'] = \
                        sds_tendrl_context['cluster_name']
                    configs.append({
                        'plugin': "ceph_cluster_iops",
                        'plugin_conf': plugin_config,
                        'node_id': node_id,
                        'fqdn': sds_node_context['fqdn']
                    })
            is_configured = True
            if (
                "ceph_node_network_throughput" not in
                    self.configured_nodes.get(node_id, [])
            ):
                plugin_config['cluster_network'] = ' '.join(
                    self.get_nw_node_interfaces(
                        node_id,
                        'cluster_network',
                        sds_tendrl_context['integration_id']
                    )
                )
                plugin_config['public_network'] = ' '.join(
                    self.get_nw_node_interfaces(
                        node_id,
                        'public_network',
                        sds_tendrl_context['integration_id']
                    )
                )
                if (
                    plugin_config['cluster_network'] and
                        plugin_config['public_network']
                ):
                    node_plugins = self.configured_nodes.get(node_id, [])
                    node_plugins.append(
                        "ceph_node_network_throughput"
                    )
                    configs.append({
                        'plugin': "%s_node_network_throughput" % self.name,
                        'plugin_conf': plugin_config,
                        'node_id': node_id,
                        'fqdn': sds_node_context['fqdn']
                    })
        return configs

    def get_nw_node_interfaces(self, node_id, nw_type, cluster_id):
        nw_node_interfaces = []
        try:
            nw_subnet = etcd_read_key(
                '/clusters/%s/maps/config/data/%s' % (
                    cluster_id,
                    nw_type
                )
            )[nw_type]
            if nw_subnet:
                nw_subnet = nw_subnet.replace('/', '_')
                networks = etcd_read_key(
                    '/networks/%s/%s' % (nw_subnet, node_id)
                )
                for interface_id, interface_det in networks.iteritems():
                    nw_node_interfaces.append(
                        interface_det.get('interface')
                    )
        except Exception:
            pass
        return nw_node_interfaces

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

    def get_rbd_status_wise_counts(self, cluster_id, cluster_det):
        # No status for rbds so currently only alert counters will be available
        rbd_status_wise_counts = {
            pm_consts.CRITICAL_ALERTS: 0,
            pm_consts.WARNING_ALERTS: 0,
            pm_consts.TOTAL: 0
        }
        for pool_id, pool_det in cluster_det.get('Pools', {}).iteritems():
            rbd_status_wise_counts[pm_consts.TOTAL] = \
                rbd_status_wise_counts[pm_consts.TOTAL] + len(pool_det.get(
                    'Rbds',
                    {}
                ).keys()
            )
        crit_alerts, warn_alerts = parse_resource_alerts(
            'rbd',
            pm_consts.CLUSTER,
            cluster_id=cluster_id
        )
        rbd_status_wise_counts[
            pm_consts.CRITICAL_ALERTS
        ] = len(crit_alerts)
        rbd_status_wise_counts[
            pm_consts.WARNING_ALERTS
        ] = len(warn_alerts)
        return rbd_status_wise_counts

    def get_pool_status_wise_counts(self, cluster_id, cluster_det):
        # No status for pools, so only alert counters will be available
        pool_status_wise_counts = {
            pm_consts.CRITICAL_ALERTS: 0,
            pm_consts.WARNING_ALERTS: 0,
            pm_consts.TOTAL: 0
        }
        pool_status_wise_counts[pm_consts.TOTAL] = \
            len(cluster_det.get('Pools', {}).keys())
        crit_alerts, warn_alerts = parse_resource_alerts(
            'pool',
            pm_consts.CLUSTER,
            cluster_id=cluster_id
        )
        pool_status_wise_counts[
            pm_consts.CRITICAL_ALERTS
        ] = len(crit_alerts)
        pool_status_wise_counts[
            pm_consts.WARNING_ALERTS
        ] = len(warn_alerts)
        return pool_status_wise_counts

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
        osd_status_wise_counts = {
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
                    osd_status_wise_counts['down'] = \
                        osd_status_wise_counts['down'] + 1
                osd_status_wise_counts['total'] = \
                    osd_status_wise_counts['total'] + 1
        crit_alerts, warn_alerts = parse_resource_alerts(
            'osd',
            pm_consts.CLUSTER,
            cluster_id=cluster_det.get(
                'TendrlContext',
                {}
            ).get('integration_id', '')
        )
        osd_status_wise_counts[
            pm_consts.CRITICAL_ALERTS
        ] = len(crit_alerts)
        osd_status_wise_counts[
            pm_consts.WARNING_ALERTS
        ] = len(warn_alerts)
        return osd_status_wise_counts

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

    def get_pg_counts(self, cluster_det):
        pg_summary = cluster_det['maps']['pg_summary']['data']['all']
        if isinstance(pg_summary, basestring):
            pg_summary = ast.literal_eval(pg_summary)
        return _calculate_pg_counters(
            pg_summary
        )

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
        ret_val['osd_status_wise_counts'] = self.get_osd_status_wise_counts(
            cluster_det
        )
        ret_val['rbd_status_wise_counts'] = \
            self.get_rbd_status_wise_counts(cluster_id, cluster_det)
        ret_val['mon_status_wise_counts'] = \
            self.get_mon_status_wise_counts(cluster_det)
        ret_val['pool_status_wise_counts'] = \
            self.get_pool_status_wise_counts(cluster_id, cluster_det)
        ret_val['pg_status_wise_counts'] = self.get_pg_counts(cluster_det)
        throughput = {}
        throughput['cluster_network'] = self.get_cluster_throughput(
            'cluster_network',
            cluster_det.get('nodes', {}),
            cluster_id
        )
        throughput['public_network'] = self.get_cluster_throughput(
            'public_network',
            cluster_det.get('nodes', {}),
            cluster_id
        )
        ret_val['throughput'] = throughput
        return ret_val

    def get_system_throughput(self, cluster_summaries):
        cluster_throughput = 0.0
        public_throughput = 0.0
        cnt = 0
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_throughput = \
                    cluster_throughput + cluster_summary.sds_det.get(
                        'throughput',
                        {}
                    ).get('cluster_network')
                cnt = cnt + 1
        if cnt > 0:
            cluster_throughput = (cluster_throughput * 1.0) / (cnt * 1.0)
        NS.time_series_db_manager.get_plugin().push_metrics(
            NS.time_series_db_manager.get_timeseriesnamefromresource(
                sds_type=self.name,
                network_type='cluster_network',
                resource_name=pm_consts.SYSTEM_THROUGHPUT,
                utilization_type=pm_consts.USED
            ),
            cluster_throughput
        )
        cnt = 0
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                public_throughput = \
                    public_throughput + cluster_summary.sds_det.get(
                        'throughput',
                        {}
                    ).get('public_network')
                cnt = cnt + 1
        if cnt > 0:
            public_throughput = (public_throughput * 1.0) / (cnt * 1.0)
        NS.time_series_db_manager.get_plugin().push_metrics(
            NS.time_series_db_manager.get_timeseriesnamefromresource(
                sds_type=self.name,
                network_type='public_network',
                resource_name=pm_consts.SYSTEM_THROUGHPUT,
                utilization_type=pm_consts.USED
            ),
            public_throughput
        )
        return {
            'cluster_network': cluster_throughput,
            'public_network': public_throughput
        }

    def get_system_pg_counts(self, cluster_summaries):
        system_pg_counts = {}
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_pg_counts = cluster_summary.sds_det.get(
                    'pg_status_wise_counts',
                    {}
                )
                for status, counter in cluster_pg_counts.iteritems():
                    counts = system_pg_counts.get('status', 0)
                    system_pg_counts[status] = counts + counter
        return system_pg_counts

    def get_system_mon_status_wise_counts(self, cluster_summaries):
        mon_status_wise_counts = {}
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_mon_count = \
                    cluster_summary.sds_det.get('mon_status_wise_counts', {})
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
                    cluster_summary.sds_det.get('osd_status_wise_counts', {})
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

    def get_system_pool_status_wise_counts(self, cluster_summaries):
        pool_status_wise_counts = {}
        pool_critical_alerts = 0
        pool_warning_alerts = 0
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_pool_count = \
                    cluster_summary.sds_det.get('pool_status_wise_counts', {})
                if (
                    isinstance(cluster_pool_count, unicode) and not
                        isinstance(cluster_pool_count, dict)
                ):
                    cluster_pool_count = ast.literal_eval(
                        cluster_pool_count.encode('ascii', 'ignore')
                    )
                for status, count in cluster_pool_count.iteritems():
                    if isinstance(count, int):
                        pool_status_wise_counts[status] = \
                            pool_status_wise_counts.get(status, 0) + count
                pool_critical_alerts = \
                    pool_critical_alerts + cluster_pool_count.get(
                        pm_consts.CRITICAL_ALERTS
                    )
                pool_warning_alerts = \
                    pool_warning_alerts + cluster_pool_count.get(
                        pm_consts.WARNING_ALERTS
                    )
        pool_status_wise_counts[pm_consts.WARNING_ALERTS] = \
            pool_warning_alerts
        pool_status_wise_counts[pm_consts.CRITICAL_ALERTS] = \
            pool_critical_alerts
        return pool_status_wise_counts

    def get_system_rbd_status_wise_counts(self, cluster_summaries):
        rbd_status_wise_counts = {}
        rbd_critical_alerts = 0
        rbd_warning_alerts = 0
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_rbd_count = \
                    cluster_summary.sds_det.get('rbd_status_wise_counts', {})
                if (
                    isinstance(cluster_rbd_count, unicode) and not
                        isinstance(cluster_rbd_count, dict)
                ):
                    cluster_rbd_count = ast.literal_eval(
                        cluster_rbd_count.encode('ascii', 'ignore')
                    )
                for status, count in cluster_rbd_count.iteritems():
                    if isinstance(count, int):
                        rbd_status_wise_counts[status] = \
                            rbd_status_wise_counts.get(status, 0) + count
                rbd_critical_alerts = \
                    rbd_critical_alerts + cluster_rbd_count.get(
                        pm_consts.CRITICAL_ALERTS
                    )
                rbd_warning_alerts = \
                    rbd_warning_alerts + cluster_rbd_count.get(
                        pm_consts.WARNING_ALERTS
                    )
        rbd_status_wise_counts[pm_consts.WARNING_ALERTS] = \
            rbd_warning_alerts
        rbd_status_wise_counts[pm_consts.CRITICAL_ALERTS] = \
            rbd_critical_alerts
        return rbd_status_wise_counts

    def compute_system_summary(self, cluster_summaries, clusters):
        try:
            SystemSummary(
                utilization=self.get_system_utilization(cluster_summaries),
                hosts_count=self.get_system_host_status_wise_counts(
                    cluster_summaries
                ),
                cluster_count=self.get_clusters_status_wise_counts(clusters),
                sds_det={
                    'mon_status_wise_counts': self.get_system_mon_status_wise_counts(
                        cluster_summaries
                    ),
                    'osd_status_wise_counts': self.get_system_osd_status_wise_counts(
                        cluster_summaries
                    ),
                    'pool_status_wise_counts': self.get_system_pool_status_wise_counts(
                        cluster_summaries
                    ),
                    'rbd_status_wise_counts': self.get_system_rbd_status_wise_counts(
                        cluster_summaries
                    ),
                    'most_used_pools': self.get_system_max_used_pools(
                        cluster_summaries
                    ),
                    'most_used_rbds': self.get_system_max_used_rbds(
                        cluster_summaries
                    ),
                    'pg_status_wise_counts': self.get_system_pg_counts(
                        cluster_summaries
                    ),
                    'throughput': self.get_system_throughput(cluster_summaries)
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

    def get_node_osd_status_wise_counts(self, node_id):
        osds_in_node = []
        osd_status_wise_counts = {
            'total': 0,
            'down': 0,
            pm_consts.CRITICAL_ALERTS: 0,
            pm_consts.WARNING_ALERTS: 0
        }
        cluster_id = NS.central_store_thread.get_node_cluster_id(
            node_id
        )
        node_ip = ''
        ip_indexes = etcd_read_key('/indexes/ip')
        for ip, indexed_node_id in ip_indexes.iteritems():
            if node_id == indexed_node_id:
                node_ip = ip
        try:
            osds = etcd_read_key(
                '/clusters/%s/maps/osd_map/data/osds' % cluster_id
            )
            osds = ast.literal_eval(osds.get('osds', '[]'))
            for osd in osds:
                if (
                    node_ip in osd.get('cluster_addr', '') or
                    node_ip in osd.get('public_addr', '')
                ):
                    osds_in_node.append(osd.get('osd'))
                    if 'up' not in osd.get('state'):
                        osd_status_wise_counts['down'] = \
                            osd_status_wise_counts['down'] + 1
                    osd_status_wise_counts['total'] = \
                        osd_status_wise_counts['total'] + 1
            crit_alerts, warn_alerts = parse_resource_alerts(
                'osd',
                pm_consts.CLUSTER,
                cluster_id=cluster_id
            )
            count = 0
            for alert in crit_alerts:
                plugin_instance = alert['tags'].get('plugin_instance', '')
                if int(plugin_instance[len('osd_'):]) in osds_in_node:
                    count = count + 1
            osd_status_wise_counts[
                pm_consts.CRITICAL_ALERTS
            ] = count
            count = 0
            for alert in warn_alerts:
                plugin_instance = alert['tags'].get('plugin_instance', '')
                if int(plugin_instance[len('osd_'):]) in osds_in_node:
                    count = count + 1
            osd_status_wise_counts[
                pm_consts.WARNING_ALERTS
            ] = count
        except Exception as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": "Exception caught computing node osd "
                                        "counts",
                             "exception": ex
                             }
                )
            )
        return osd_status_wise_counts

    def get_node_summary(self, node_id):
        ret_val = {}
        ret_val['osd_status_wise_counts'] = self.get_node_osd_status_wise_counts(
            node_id
        )
        return ret_val
