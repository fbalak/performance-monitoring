from tendrl.common.config import TendrlConfig
from tendrl.common.etcdobj.etcdobj import Server as etcd_server
from tendrl.performance_monitoring.defaults.default_values\
    import GetMonitoringDefaults


config = TendrlConfig()

MONITORING_CONFIG_DIRECTORY = "/_tendrl/config/performance_monitoring"


class DefaultsManager(object):

    def __init__(self):
        etcd_kwargs = {
            'port': int(config.get("common", "etcd_port")),
            'host': config.get("common", "etcd_connection")
        }
        self.etcd_client = etcd_server(etcd_kwargs=etcd_kwargs).client
        self.init_monitoring_configs(
            MONITORING_CONFIG_DIRECTORY,
            GetMonitoringDefaults().getDefaults())

    def init_monitoring_configs(self, etcd_dir, configs):
        self.etcd_client.write(etcd_dir, str(configs))
