from abc import abstractmethod
import importlib
import inspect
import logging
import os
import re
import six
from tendrl.common.config import ConfigNotFound
from tendrl.common.config import TendrlConfig
from tendrl.common.singleton import to_singleton


LOG = logging.getLogger(__name__)
config = TendrlConfig()


class FailedToFetchTimeSeriesData(Exception):

    def __init__(self, err_msg):
        self.msg = err_msg


class PluginMount(type):

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.register_plugin(cls)

    def register_plugin(cls, plugin):
        instance = plugin()
        cls.plugins.append(instance)
        instance.intialize()


@six.add_metaclass(PluginMount)
class TimeSeriesDBPlugin(object):

    @abstractmethod
    def intialize(self):
        raise NotImplementedError()

    @abstractmethod
    def get_metric_stats(self, entity_name, metric_name):
        raise NotImplementedError()

    @abstractmethod
    def get_metrics(self, entity_name):
        raise NotImplementedError()

    @abstractmethod
    def destroy(self):
        raise NotImplementedError()


@to_singleton
class TimeSeriesDBManager(object):

    def __init__(self):
        self.time_series_db = config.get('time_series', 'time_series_db')
        try:
            self.load_plugins()
        except (ConfigNotFound, SyntaxError, ValueError, ImportError) as ex:
            raise ex
        self.plugin = self.set_plugin()

    def load_plugins(self):
        try:
            path = os.path.dirname(os.path.abspath(__file__)) + '/dbplugins'
            pkg = 'tendrl.performance_monitoring.time_series_db.dbplugins'
            for py in [f[:-3] for f in os.listdir(path)
                       if f.endswith('.py') and f != '__init__.py']:
                plugin_name = '.'.join([pkg, py])
                mod = importlib.import_module(plugin_name)
                clsmembers = inspect.getmembers(mod, inspect.isclass)
                for name, cls in clsmembers:
                    exec("from %s import %s" % (plugin_name, name))
        except (ConfigNotFound, SyntaxError, ValueError, ImportError) as ex:
            LOG.error('Failed to load the time series db plugins. Error %s' %
                      ex, exc_info=True)
            raise ex

    def get_plugin(self):
        return self.plugin

    def set_plugin(self):
        for plugin in TimeSeriesDBPlugin.plugins:
            if re.search(self.time_series_db.lower(), type(
                    plugin).__name__.lower(), re.IGNORECASE):
                return plugin

    def stop(self):
        self.plugin.destroy()
