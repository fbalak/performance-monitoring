from tendrl.performance_monitoring.defaults.default_values\
    import GetMonitoringDefaults
import yaml


MONITORING_CONFIG_DIRECTORY = "/_tendrl/config/performance_monitoring"


class DefaultsManager(object):

    def __init__(self, persister, api_host, api_port):
        self.etcd_client = persister.get_store().client
        self.init_monitoring_configs(
            MONITORING_CONFIG_DIRECTORY,
            GetMonitoringDefaults(api_host, api_port).getDefaults())

    def init_monitoring_configs(self, etcd_dir, configs):
        self.etcd_client.write(etcd_dir, yaml.safe_dump(configs))
