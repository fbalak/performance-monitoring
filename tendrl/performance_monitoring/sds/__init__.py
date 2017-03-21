from abc import abstractmethod
import importlib
import inspect
import logging
import os
from tendrl.commons.utils.etcd_util import read as etcd_read_key
from tendrl.performance_monitoring.utils import list_modules_in_package_path
import six


LOG = logging.getLogger(__name__)


class NoSDSPluginException(Exception):
    pass


class PluginMount(type):

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.register_plugin(cls)

    def register_plugin(cls, plugin):
        instance = plugin()
        cls.plugins.append(instance)


@six.add_metaclass(PluginMount)
class SDSPlugin(object):
    name = ''

    @abstractmethod
    def configure_monitoring(self, sds_tendrl_context):
        raise NotImplementedError(
            "The plugins overriding SDSPlugin should mandatorily ovveride this"
        )


class SDSMonitoringManager(object):
    def load_sds_plugins(self):
        path = os.path.dirname(os.path.abspath(__file__))
        pkg = 'tendrl.performance_monitoring.sds'
        sds_plugins = list_modules_in_package_path(path, pkg)
        for name, sds_fqdn in sds_plugins:
            mod = importlib.import_module(sds_fqdn)
            clsmembers = inspect.getmembers(mod, inspect.isclass)
            for name, cls in clsmembers:
                if cls.name:
                    self.supported_sds.append(cls.name)

    def __init__(self):
        self.supported_sds = []
        self.load_sds_plugins()

    def configure_monitoring(self, integration_id):
        try:
            sds_tendrl_context = etcd_read_key(
                'clusters/%s/TendrlContext' % integration_id
            )
        except Exception as ex:
            LOG.error(
                'Failed to configure monitoring for cluster %s as tendrl'
                ' context could not be fetched. Error %s' % (
                    integration_id,
                    str(ex)
                )
            )
            return
        for plugin in SDSPlugin.plugins:
            if plugin.name == sds_tendrl_context['sds_name']:
                return plugin.configure_monitoring(sds_tendrl_context)
        LOG.error(
            'No plugin defined for %s. Hence cannot configure it' % (
                sds_tendrl_context['sds_name']
            ),
            exc_info=True
        )
        return None
