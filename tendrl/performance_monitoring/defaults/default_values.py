import logging
import socket
from tendrl.common.config import ConfigNotFound
from tendrl.common.config import TendrlConfig
import yaml


LOG = logging.getLogger(__name__)

DEFAULT_PATH = '/etc/tendrl/monitoring_defaults.yaml'

tendrl_config = TendrlConfig()


class GetMonitoringDefaults(object):
    def __init__(self, defaults_path=None):
        if defaults_path is None:
            self.defaults_path = DEFAULT_PATH
        else:
            self.defaults_path = defaults_path
        self.defaults = {}
        self.setDefaults()

    def getDefaults(self):
        return self.defaults

    def setDefaults(self):
        try:
            data = open(self.defaults_path)
            config = yaml.load(data)
            self.defaults = config
            self.defaults['master_name'] = socket.getfqdn()
            api_server_addr = tendrl_config.get(
                "tendrl_performance",
                "api_server_addr"
            )
            if api_server_addr == '0.0.0.0':
                api_server_addr = socket.getfqdn()
            self.defaults['api_server'] = {
                "api_server_addr": api_server_addr,
                "api_server_port": tendrl_config.get(
                    "tendrl_performance",
                    "api_server_port"
                )
            }
        except (IOError, yaml.YAMLError, AttributeError, ConfigNotFound) as ex:
            LOG.info('Fetching defaults failed from path %s. Error %s'
                     % (self.defaults_path, ex))
