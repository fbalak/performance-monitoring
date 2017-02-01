from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import config as cmn_config

from tendrl.node_monitoring import objects


class Config(objects.NodeMonitoringBaseObject):
    def __init__(self, config=None, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

        self.value = '_tendrl/config/node_monitoring/data'
        self.data = config or cmn_config.load_config(
            'node_monitoring',
            "/etc/tendrl/node-monitoring/node-monitoring.conf.yaml"
        )
        self._etcd_cls = _ConfigEtcd


class _ConfigEtcd(EtcdObj):
    """Config etcd object, lazily updated

    """
    __name__ = '_tendrl/config/node_monitoring/'
    _tendrl_cls = Config
