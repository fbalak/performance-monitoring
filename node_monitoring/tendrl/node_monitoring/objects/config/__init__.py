from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons import config as cmn_config
from tendrl.commons.objects import BaseObject


class Config(BaseObject):
    internal = True
    def __init__(self, config=None, *args, **kwargs):
        self._defs = {}
        super(Config, self).__init__(*args, **kwargs)

        self.value = '_NS/node_monitoring/config'
        self.data = config or cmn_config.load_config(
            'node_monitoring',
            "/etc/tendrl/node-monitoring/node-monitoring.conf.yaml"
        )
        self._etcd_cls = _ConfigEtcd


class _ConfigEtcd(EtcdObj):
    """Config etcd object, lazily updated

    """
    __name__ = '_NS/node_monitoring/config'
    _tendrl_cls = Config
