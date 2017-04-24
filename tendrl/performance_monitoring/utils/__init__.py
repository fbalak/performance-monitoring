from etcd import EtcdConnectionFailed
from etcd import EtcdException
import json
import pkgutil
from tendrl.commons.objects.job import Job
from tendrl.performance_monitoring import constants as \
    pm_consts
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
import uuid


def list_modules_in_package_path(package_path, prefix):
    modules = []
    path_to_walk = [(package_path, prefix)]
    while len(path_to_walk) > 0:
        curr_path, curr_prefix = path_to_walk.pop()
        for importer, name, ispkg in pkgutil.walk_packages(
            path=[curr_path]
        ):
            if ispkg:
                path_to_walk.append(
                    (
                        '%s/%s/' % (curr_path, name),
                        '%s.%s' % (curr_prefix, name)
                    )
                )
            else:
                modules.append((name, '%s.%s' % (curr_prefix, name)))
    return modules


def initiate_config_generation(node_det):
    try:
        job_params = {
            'node_ids': [node_det.get('node_id')],
            "run": 'node_monitoring.flows.ConfigureCollectd',
            'type': 'monitoring',
            "parameters": {
                'plugin_name': node_det['plugin'],
                'plugin_conf_params': json.dumps(
                    node_det['plugin_conf']
                ).encode('utf-8'),
                'Node.fqdn': node_det['fqdn'],
                'Service.name': 'collectd',
            },
        }
        Job(
            job_id=str(uuid.uuid4()),
            status='new',
            payload=json.dumps(job_params).encode('utf-8'),
        ).save()
    except (EtcdException, EtcdConnectionFailed, Exception) as ex:
        raise TendrlPerformanceMonitoringException(
            'Failed to intiate monitoring configuration for plugin \
            %s on %s with parameters %s.Error %s' % (
                node_det['plugin'],
                node_det['fqdn'],
                json.dumps(node_det['plugin_conf']),
                str(ex)
            )
        )


# this function can return json for any etcd key
def read(key):
    result = {}
    job = NS.etcd_orm.client.read(key)
    if hasattr(job, 'leaves'):
        for item in job.leaves:
            if item.dir is True:
                result[item.key.split("/")[-1]] = read(item.key)
            else:
                result[item.key.split("/")[-1]] = item.value
    return result


def parse_resource_alerts(resource_type, resource_classification, **kwargs):
    alerts = {}
    if resource_classification == pm_consts.NODE:
        alerts = NS.central_store_thread.get_node_alerts(
            **kwargs
        )
    if resource_classification == pm_consts.CLUSTER:
        alerts = NS.central_store_thread.get_cluster_alerts(
            **kwargs
        )
    critical_alerts = []
    warning_alerts = []
    for alert in alerts:
        if (
            alert['acked'] == "True" or
            alert['acked'] == "true"
        ):
            continue
        if resource_type:
            for alert_type in pm_consts.SUPPORTED_ALERT_TYPES:
                if alert['resource'] == '%s_%s' % (resource_type, alert_type):
                    if alert['severity'] == pm_consts.CRITICAL:
                        critical_alerts.append(alert)
                    if alert['severity'] == pm_consts.WARNING:
                        warning_alerts.append(alert)
        else:
            if alert['severity'] == pm_consts.CRITICAL:
                critical_alerts.append(alert)
            if alert['severity'] == pm_consts.WARNING:
                warning_alerts.append(alert)
    return critical_alerts, warning_alerts
