from abc import abstractmethod
import importlib
import inspect
import logging
import os
import re
import six


LOG = logging.getLogger(__name__)
config = None


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
        instance.intialize(config)


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


class TimeSeriesDBManager(object):

    def __init__(self, conf, time_series_db):
        # Since this is a singleton class the singleton framework ensures only
        # a single call to this constructor in the life time of the application
        # However wherever the class is attempted to be intialized, it tries to
        # match the constructor and hence the 2nd arguement is made to appear
        # as an optional arguement although it is enforced internally not be
        # optional due to reason stated above.
        self.time_series_db = time_series_db
        global config
        config = conf
        try:
            self.load_plugins()
        except (SyntaxError, ValueError, ImportError) as ex:
            raise ex
        self.plugin = None
        self.set_plugin()

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
        except (SyntaxError, ValueError, ImportError) as ex:
            LOG.error('Failed to load the time series db plugins. Error %s' %
                      ex, exc_info=True)
            raise ex

    def get_plugin(self):
        return self.plugin

    def set_plugin(self):
        for plugin in TimeSeriesDBPlugin.plugins:
            if re.search(self.time_series_db.lower(), type(
                    plugin).__name__.lower(), re.IGNORECASE):
                self.plugin = plugin

    def stop(self):
        self.plugin.destroy()

