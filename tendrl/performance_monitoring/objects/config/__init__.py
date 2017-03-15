import socket
from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import config as cmn_config
from tendrl.commons.objects import BaseObject
from tendrl.performance_monitoring.defaults.default_values\
    import GetMonitoringDefaults


class Config(BaseObject):
    def __init__(self, config=None, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

        self.value = '_NS/performance_monitoring/config'
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
    __name__ = '_NS/performance_monitoring/config'
    _tendrl_cls = Config
