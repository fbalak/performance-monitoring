import socket
from tendrl.commons.etcdobj.etcdobj import EtcdObj
from tendrl.commons import config as cmn_config

from tendrl.performance_monitoring.defaults.default_values\
    import GetMonitoringDefaults
from tendrl.performance_monitoring.objects \
    import PerformanceMonitoringBaseObject


class Config(PerformanceMonitoringBaseObject):
    def __init__(self, config=None, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

        self.value = '_tendrl/config/performance_monitoring/data'
        if config is None:
            config = cmn_config.load_config(
                'performance_monitoring',
                "/etc/tendrl/performance-monitoring/performance-monitoring.conf.yaml"
            )
            config.update(
                GetMonitoringDefaults().getDefaults()
            )
            if config['api_server_addr'] == '0.0.0.0':
                config['api_server_addr'] = socket.getfqdn()
        self.data = config
        self._etcd_cls = _ConfigEtcd


class _ConfigEtcd(EtcdObj):
    """Config etcd object, lazily updated

    """
    __name__ = '_tendrl/config/performance_monitoring/'
    _tendrl_cls = Config
