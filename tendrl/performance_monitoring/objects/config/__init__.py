import socket

from tendrl.commons import config as cmn_config
from tendrl.commons import objects
from tendrl.performance_monitoring.defaults.default_values\
    import GetMonitoringDefaults


class Config(objects.BaseObject):

    internal = True

    def __init__(self, config=None, *args, **kwargs):
        self._defs = {}
        super(Config, self).__init__(*args, **kwargs)

        if config is None:
            config = cmn_config.load_config(
                'performance_monitoring',
                "/etc/tendrl/performance-monitoring/performance-monitoring."
                "conf.yaml"
            )
            config.update(
                GetMonitoringDefaults().getDefaults()
            )
            if config['api_server_addr'] == '0.0.0.0':
                config['api_server_addr'] = socket.getfqdn()
        self.data = config
        self.value = '_NS/performance_monitoring/config'
