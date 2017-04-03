from ruamel import yaml
import socket

from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage

DEFAULT_PATH = '/etc/tendrl/performance-monitoring/monitoring_defaults.yaml'


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
        except (IOError, yaml.YAMLError, AttributeError) as ex:
            Event(
                ExceptionMessage(
                    priority="info",
                    publisher=NS.publisher_id,
                    payload={"message": 'Fetching defaults failed from path '
                                        '%s.' % self.defaults_path,
                             "exception": ex
                             }
                )
            )
