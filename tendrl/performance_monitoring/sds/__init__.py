from abc import abstractmethod
import importlib
import inspect
import logging
import os
from tendrl.commons.utils.etcd_util import read as etcd_read_key
from tendrl.performance_monitoring.utils import list_modules_in_package_path
import six


LOG = logging.getLogger(__name__)


class NoSDSPluginException(Exception):
    pass


class PluginMount(type):

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.register_plugin(cls)

    def register_plugin(cls, plugin):
        instance = plugin()
        cls.plugins.append(instance)


@six.add_metaclass(PluginMount)
class SDSPlugin(object):
    name = ''

    def __init__(self):
        self.supported_services = [
            'tendrl-node-agent',
            'etcd'
        ]

    @abstractmethod
    def configure_monitoring(self, sds_tendrl_context):
        raise NotImplementedError(
            "The plugins overriding SDSPlugin should mandatorily override this"
        )

    @abstractmethod
    def get_cluster_summary(self, cluster_id, cluster_det):
        raise NotImplementedError(
            "The plugins overriding SDSPlugin should mandatorily override this"
        )

    @abstractmethod
    def compute_system_summary(self, cluster_summaries, clusters):
        raise NotImplementedError(
            "The plugins overriding SDSPlugin should mandatorily override this"
        )

    def get_clusters_status_wise_counts(self, clusters):
        clusters_status_wise_counts = {'total': 0}
        for cluster_id, cluster_det in clusters.iteritems():
            if (
                self.name in
                    cluster_det.get('TendrlContext', {}).get('sds_name')
            ):
                cluster_status = cluster_det.get(
                    'GlobalDetails', {}
                ).get('status')
                if cluster_status:
                    if cluster_status not in clusters_status_wise_counts:
                        clusters_status_wise_counts[cluster_status] = 1
                    else:
                        clusters_status_wise_counts[cluster_status] = \
                            clusters_status_wise_counts[cluster_status] + 1
                    clusters_status_wise_counts['total'] = \
                        clusters_status_wise_counts['total'] + 1
        return clusters_status_wise_counts

    def get_system_utilization(self, cluster_summaries):
        net_utilization = {
            'total': 0,
            'used': 0,
            'percent_used': 0
        }
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                net_utilization['total'] = \
                    net_utilization['total'] + cluster_summary.utilization.get(
                        'total', 0
                )
                net_utilization['used'] = \
                    net_utilization['used'] + cluster_summary.utilization.get(
                        'used', 0
                )
                if net_utilization['total'] > 0:
                    net_utilization['percent_used'] = (
                        net_utilization['used'] * 100
                    ) / (
                        net_utilization['total'] * 1.0
                    )
        return net_utilization

    def get_system_host_status_wise_counts(self, cluster_summaries):
        status_wise_count = {
            'total': 0,
            'down': 0,
            'crit_alert_count': 0,
            'warn_alert_count': 0
        }
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                for status, counter in cluster_summary.hosts_count.iteritems():
                    status_wise_count[status] = \
                        status_wise_count.get(status, 0) + counter
        return status_wise_count

    def get_services_count(self, cluster_det):
        node_service_counts = {}
        for node_id, node_det in cluster_det.get('nodes', {}).iteritems():
            services = etcd_read_key('nodes/%s/Service' % node_id)
            for service_name, service_det in services.iteritems():
                if service_name in self.supported_services:
                    if service_name not in node_service_counts:
                        service_counter = {'running': 0, 'not_running': 0}
                    else:
                        service_counter = node_service_counts[service_name]
                    if service_det['exists'] == 'True':
                        if service_det['running'] == 'True':
                            service_counter['running'] = \
                                service_counter['running'] + 1
                        else:
                            service_counter['not_running'] = \
                                service_counter['not_running'] + 1
                        node_service_counts[service_name] = service_counter
        return node_service_counts

    def get_system_services_count(self, cluster_summaries):
        system_services_count = {}
        for cluster_summary in cluster_summaries:
            if self.name in cluster_summary.sds_type:
                for service_name, service_status_counter in \
                        cluster_summary.get('services_count').iteritems():
                    service_counter = {}
                    for service_status, counter in \
                            service_status_counter.iteritems():
                        service_counter[service_status] = \
                            service_counter.get(service_status, 0) + counter
                    system_services_count[service_name] = service_counter
        return system_services_count


class SDSMonitoringManager(object):
    def load_sds_plugins(self):
        path = os.path.dirname(os.path.abspath(__file__))
        pkg = 'tendrl.performance_monitoring.sds'
        sds_plugins = list_modules_in_package_path(path, pkg)
        for name, sds_fqdn in sds_plugins:
            mod = importlib.import_module(sds_fqdn)
            clsmembers = inspect.getmembers(mod, inspect.isclass)
            for name, cls in clsmembers:
                if isinstance(cls, SDSPlugin):
                    if cls.name:
                        self.supported_sds.append(cls.name)

    def __init__(self):
        self.supported_sds = []
        self.load_sds_plugins()

    def get_cluster_summary(self, cluster_id, cluster_det):
        sds_name = cluster_det.get('TendrlContext', {}).get('sds_name')
        for plugin in SDSPlugin.plugins:
            if plugin.name == sds_name:
                return plugin.get_cluster_summary(cluster_id, cluster_det)

    def compute_system_summary(self, cluster_summaries, clusters):
        for plugin in SDSPlugin.plugins:
            plugin.compute_system_summary(cluster_summaries, clusters)

    def configure_monitoring(self, integration_id):
        try:
            sds_tendrl_context = etcd_read_key(
                'clusters/%s/TendrlContext' % integration_id
            )
        except Exception as ex:
            LOG.error(
                'Failed to configure monitoring for cluster %s as tendrl'
                ' context could not be fetched. Error %s' % (
                    integration_id,
                    str(ex)
                )
            )
            return
        for plugin in SDSPlugin.plugins:
            if plugin.name == sds_tendrl_context['sds_name']:
                return plugin.configure_monitoring(sds_tendrl_context)
        LOG.error(
            'No plugin defined for %s. Hence cannot configure it' % (
                sds_tendrl_context['sds_name']
            ),
            exc_info=True
        )
        return None
