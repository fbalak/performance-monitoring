import logging
import socket
import yaml


LOG = logging.getLogger(__name__)

DEFAULT_PATH = '/etc/tendrl/monitoring_defaults.yaml'


class GetMonitoringDefaults(object):
    def __init__(self, api_host, api_port, defaults_path=None):
        if defaults_path is None:
            self.defaults_path = DEFAULT_PATH
        else:
            self.defaults_path = defaults_path
        self.defaults = {}
        if api_host == '0.0.0.0':
                api_host = socket.getfqdn()
        self.defaults['api_server'] = {
            "api_server_addr": api_host,
            "api_server_port": api_port
        }
        self.setDefaults()

    def getDefaults(self):
        return self.defaults

    def setDefaults(self):
        try:
            data = open(self.defaults_path)
            config = yaml.load(data)
            self.defaults = config
            self.defaults['master_name'] = socket.getfqdn()
        except (IOError, yaml.YAMLError, AttributeError) as ex:
            LOG.info('Fetching defaults failed from path %s. Error %s'
                     % (self.defaults_path, ex))
