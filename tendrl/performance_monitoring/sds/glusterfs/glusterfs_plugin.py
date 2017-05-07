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


class GlusterFSPlugin(SDSPlugin):

    name = 'gluster'

    def __init__(self):
        SDSPlugin.__init__(self)
        self.supported_services.extend([
            'tendrl-gluster-integration',
            'glusterd'
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
            config = NS.performance_monitoring.config.data['thresholds']
            if isinstance(config, basestring):
                config = ast.literal_eval(config.encode('ascii', 'ignore'))
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
                        'plugin': "%sfs_%s" % (self.name, plugin),
                        'plugin_conf': plugin_config,
                        'node_id': node_id,
                        'fqdn': sds_node_context['fqdn']
                    })
            is_configured = True
            if (
                "%sfs_peer_network_throughput" % (self.name) not in
                    self.configured_nodes[node_id]
            ):
                node_plugins = self.configured_nodes[node_id]
                node_plugins.append(
                    "%sfs_peer_network_throughput" % (self.name)
                )
                is_configured = False
            if not is_configured:
                configs.append({
                    'plugin': "%sfs_peer_network_throughput" % (self.name),
                    'plugin_conf': {
                        'peer_name': sds_node_context['fqdn']
                    },
                    'node_id': node_id,
                    'fqdn': sds_node_context['fqdn']
                })
        return configs

    def get_brick_status_wise_counts(self, volumes_det, cluster_id):
        brick_status_wise_counts = {
            'stopped': 0,
            'total': 0,
            pm_consts.WARNING_ALERTS: 0,
            pm_consts.CRITICAL_ALERTS: 0
        }
        try:
            for volume_id, volume_det in volumes_det.iteritems():
                for brick_path, brick_det in volume_det.get(
                    'Bricks',
                    {}
                ).iteritems():
                    if brick_det['status'] == 'Stopped':
                        brick_status_wise_counts['stopped'] = \
                            brick_status_wise_counts['stopped'] + 1
                    brick_status_wise_counts['total'] = \
                        brick_status_wise_counts['total'] + 1
        except Exception as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": "Exception caught computing brick "
                                        "status wise counts",
                             "exception": ex
                             }
                )
            )
        crit_alerts, warn_alerts = parse_resource_alerts(
            'brick',
            pm_consts.CLUSTER,
            cluster_id=cluster_id
        )
        brick_status_wise_counts[
            pm_consts.CRITICAL_ALERTS
        ] = len(crit_alerts)
        brick_status_wise_counts[
            pm_consts.WARNING_ALERTS
        ] = len(warn_alerts)
        return brick_status_wise_counts

    def get_volume_status_wise_counts(self, cluster_det, cluster_id):
        volumes_det = cluster_det.get('Volumes', {})
        volume_status_wise_counts = {
            'down': 0,
            'total': 0,
            'degraded': 0,
            pm_consts.CRITICAL_ALERTS: 0,
            pm_consts.WARNING_ALERTS: 0
        }
        # Needs to be tested
        for vol_id, vol_det in volumes_det.iteritems():
            if 'Started' not in vol_det.get('status'):
                volume_status_wise_counts['down'] = \
                    volume_status_wise_counts['down'] + 1
            volume_status_wise_counts['total'] = \
                volume_status_wise_counts['total'] + 1
        volume_status_wise_counts['degraded'] = \
            int(cluster_det.get('GlobalDetails', {}).get(
                'volume_up_degraded',
                0
            )
        )
        crit_alerts, warn_alerts = parse_resource_alerts(
            'volume',
            pm_consts.CLUSTER,
            cluster_id=cluster_id
        )
        volume_status_wise_counts[
            pm_consts.CRITICAL_ALERTS
        ] = len(crit_alerts)
        volume_status_wise_counts[
            pm_consts.WARNING_ALERTS
        ] = len(warn_alerts)
        return volume_status_wise_counts

    def get_most_used_volumes(self, cluster_det):
        volumes_det = cluster_det.get('Volumes', {})
        # Needs to be tested
        most_used_volumes = []
        v_sort = sorted(
            volumes_det.keys(), key=lambda x: (volumes_det[x]['pcnt_used'])
        )
        v_sort.reverse()
        for volume_id in v_sort:
            vol_det = volumes_det.get(volume_id)
            vol_det['cluster_name'] = cluster_det.get(
                'TendrlContext',
                {}
            ).get('cluster_name', '')
            most_used_volumes.append(vol_det)
        return most_used_volumes[:5]

    def get_most_used_bricks(self, volumes_det, cluster_name):
        brick_utilizations = []
        try:
            for volume_id, volume_det in volumes_det.iteritems():
                for brick_path, brick_det in volume_det.get(
                    'Bricks',
                    {}
                ).iteritems():
                    if (
                        'utilization' not in brick_det or
                        not brick_det['utilization']
                    ):
                        continue
                    brick_det['utilization']['brick_path'] = brick_path
                    brick_det['utilization']['vol_name'] = volume_det['name']
                    brick_det['utilization']['cluster_name'] = cluster_name
                    brick_utilizations.append(brick_det['utilization'])
        except Exception as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": "Exception caught computing most used "
                                        "bricks",
                             "exception": ex
                             }
                )
            )
        brick_utilizations = sorted(
            brick_utilizations,
            key=lambda k: k['used_percent']
        )
        brick_utilizations.reverse()
        return brick_utilizations[:5]

    def get_cluster_summary(self, cluster_id, cluster_det):
        ret_val = {}
        ret_val['services_count'] = self.get_services_count(
            cluster_det
        )
        ret_val['volume_status_wise_counts'] = \
            self.get_volume_status_wise_counts(
                cluster_det,
                cluster_id
        )
        ret_val['brick_status_wise_counts'] = \
            self.get_brick_status_wise_counts(
                cluster_det.get('Volumes', {}),
                cluster_id
        )
        ret_val['most_used_volumes'] = self.get_most_used_volumes(
            cluster_det
        )
        ret_val['throughput'] = self.get_cluster_throughput(
            'cluster_network',
            cluster_det.get('nodes', {}),
            cluster_id
        )
        ret_val['most_used_bricks'] = self.get_most_used_bricks(
            cluster_det.get('Volumes', {}),
            cluster_det.get('TendrlContext', {}).get('cluster_name', '')
        )
        ret_val['connection_active'] = cluster_det.get(
            'GlobalDetails',
            {}
        ).get('connection_active', 0)
        ret_val['connection_count'] = cluster_det.get(
            'GlobalDetails',
            {}
        ).get('connection_count', 0)
        return ret_val

    def get_system_client_connection_counts(self, cluster_summaries):
        connection_count = 0
        connection_active = 0
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                connection_count = \
                    connection_count + int(cluster_summary.sds_det.get(
                        'connection_count',
                        0
                    ))
                connection_active = \
                    connection_active + int(cluster_summary.sds_det.get(
                        'connection_active',
                        0
                    ))
        return connection_count, connection_active

    def get_system_brick_status_wise_counts(self, cluster_summaries):
        brick_status_wise_counts = {}
        brick_critical_alerts = 0
        brick_warning_alerts = 0
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_brick_count = cluster_summary.sds_det.get(
                    'brick_status_wise_counts', {}
                )
                if isinstance(cluster_brick_count, unicode):
                    cluster_brick_count = ast.literal_eval(
                        cluster_brick_count.encode('ascii', 'replace')
                    )
                for status, count in cluster_brick_count.iteritems():
                    if isinstance(count, int):
                        brick_status_wise_counts[status] = \
                            brick_status_wise_counts.get(status, 0) + \
                            int(count)
                brick_critical_alerts = \
                    brick_critical_alerts + cluster_brick_count.get(
                        pm_consts.CRITICAL_ALERTS
                    )
                brick_warning_alerts = \
                    brick_warning_alerts + cluster_brick_count.get(
                        pm_consts.WARNING_ALERTS
                    )
        brick_status_wise_counts[pm_consts.WARNING_ALERTS] = \
            brick_warning_alerts
        brick_status_wise_counts[pm_consts.CRITICAL_ALERTS] = \
            brick_critical_alerts
        return brick_status_wise_counts

    def get_system_most_used_bricks(self, cluster_summaries):
        brick_utilizations = []
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                brick_utilizations.extend(
                    cluster_summary.sds_det['most_used_bricks']
                )
        brick_utilizations = sorted(
            brick_utilizations,
            key=lambda k: k['used_percent']
        )
        brick_utilizations.reverse()
        return brick_utilizations[:5]

    def get_system_volume_status_wise_counts(self, cluster_summaries):
        volume_status_wise_counts = {}
        volume_critical_alerts = 0
        volume_warning_alerts = 0
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_volume_count = cluster_summary.sds_det.get(
                    'volume_status_wise_counts', {}
                )
                if isinstance(cluster_volume_count, unicode):
                    cluster_volume_count = ast.literal_eval(
                        cluster_volume_count.encode('ascii', 'replace')
                    )
                for status, count in cluster_volume_count.iteritems():
                    if isinstance(count, int):
                        volume_status_wise_counts[status] = \
                            volume_status_wise_counts.get(status, 0) + \
                            int(count)
                volume_critical_alerts = \
                    volume_critical_alerts + cluster_volume_count.get(
                        pm_consts.CRITICAL_ALERTS
                    )
                volume_warning_alerts = \
                    volume_warning_alerts + cluster_volume_count.get(
                        pm_consts.WARNING_ALERTS
                    )
        volume_status_wise_counts[pm_consts.WARNING_ALERTS] = \
            volume_warning_alerts
        volume_status_wise_counts[pm_consts.CRITICAL_ALERTS] = \
            volume_critical_alerts
        return volume_status_wise_counts

    def get_system_max_used_volumes(self, cluster_summaries):
        most_used_volumes = []
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                cluster_most_used_volumes = \
                    cluster_summary.sds_det.get('most_used_volumes', {})
                if isinstance(cluster_most_used_volumes, basestring):
                    cluster_most_used_volumes = ast.literal_eval(
                        cluster_most_used_volumes.encode(
                            'ascii', 'ignore'
                        )
                    )
                for volume in cluster_most_used_volumes:
                    if isinstance(volume, unicode):
                        volume = volume.encode('ascii', 'ignore')
                        volume = ast.literal_eval(volume)
                    most_used_volumes.append(volume)
        most_used_volumes = \
            sorted(most_used_volumes, key=lambda k: k['pcnt_used'])
        most_used_volumes.reverse()
        return most_used_volumes[:5]

    def get_system_throughput(self, cluster_summaries):
        throughput = 0.0
        cnt = 0
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                throughput = throughput + cluster_summary.sds_det.get(
                    'throughput'
                )
                cnt = cnt + 1
        if cnt > 0:
            throughput = (throughput * 1.0) / (cnt * 1.0)
        NS.time_series_db_manager.get_plugin().push_metrics(
            NS.time_series_db_manager.get_timeseriesnamefromresource(
                sds_type=self.name,
                network_type='cluster_network',
                resource_name=pm_consts.SYSTEM_THROUGHPUT,
                utilization_type=pm_consts.USED
            ),
            throughput
        )
        return throughput

    def compute_system_summary(self, cluster_summaries, clusters):
        try:
            connection_count, connection_active = \
                self.get_system_client_connection_counts(cluster_summaries)
            SystemSummary(
                utilization=self.get_system_utilization(cluster_summaries),
                hosts_count=self.get_system_host_status_wise_counts(
                    cluster_summaries
                ),
                cluster_count=self.get_clusters_status_wise_counts(clusters),
                sds_det={
                    'volume_counts': self.get_system_volume_status_wise_counts(
                        cluster_summaries
                    ),
                    'most_used_volumes': self.get_system_max_used_volumes(
                        cluster_summaries
                    ),
                    'services_count': self.get_system_services_count(
                        cluster_summaries
                    ),
                    'brick_counts': self.get_system_brick_status_wise_counts(
                        cluster_summaries
                    ),
                    'most_used_bricks': self.get_system_most_used_bricks(
                        cluster_summaries
                    ),
                    'throughput': self.get_system_throughput(
                        cluster_summaries
                    ),
                    'connection_count': connection_count,
                    'connection_active': connection_active
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
