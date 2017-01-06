from mock import MagicMock
from multiprocessing import queues
import sys
sys.modules['tendrl.common.config'] = MagicMock()
sys.modules['tendrl.common.log'] = MagicMock()
from tendrl.common.etcdobj.etcdobj import Server as etcd_server
from tendrl.performance_monitoring.api.manager import APIManager
from tendrl.performance_monitoring.configure.configurator import Configurator
from tendrl.performance_monitoring.configure.configure_monitoring \
    import ConfigureMonitoring
from tendrl.performance_monitoring.defaults.manager import \
    DefaultsManager
from tendrl.performance_monitoring.manager \
    import config
from tendrl.performance_monitoring.manager \
    import TendrlPerformanceManager
del sys.modules['tendrl.common.config']
del sys.modules['tendrl.common.log']


class TestManager(object):
    def test_manager_constructor(self, monkeypatch):

        def mock_config(package, parameter):
            if parameter == "etcd_port":
                return '0'
            elif parameter == "etcd_connection":
                return '0.0.0.0'

        monkeypatch.setattr(config, 'get', mock_config)
        manager = TendrlPerformanceManager()
        assert isinstance(manager.etcd_server, etcd_server)
        assert isinstance(manager.api_manager, APIManager)
        assert isinstance(manager.defaults_manager, DefaultsManager)
        assert isinstance(manager.configurator_queue, queues.Queue)
        assert isinstance(manager.configure_monitoring, ConfigureMonitoring)
        assert isinstance(manager.configurator, Configurator)

    def test_start(self, monkeypatch):

        def mock_config(package, parameter):
            if parameter == "etcd_port":
                return '0'
            elif parameter == "etcd_connection":
                return '0.0.0.0'
        monkeypatch.setattr(config, 'get', mock_config)
        manager = TendrlPerformanceManager()

        def mock_load_defs():
            return

        def mock_start():
            return

        monkeypatch.setattr(manager, 'start', mock_start)
        monkeypatch.setattr(manager, 'load_defs', mock_load_defs)
        manager.start()

    def test_stop(self, monkeypatch):

        def mock_config(package, parameter):
            if parameter == "etcd_port":
                return '0'
            elif parameter == "etcd_connection":
                return '0.0.0.0'

        monkeypatch.setattr(config, 'get', mock_config)
        manager = TendrlPerformanceManager()

        def mock_load_defs():
            return

        def mock_stop():
            return

        monkeypatch.setattr(manager, 'stop', mock_stop)
        monkeypatch.setattr(manager, 'load_defs', mock_load_defs)
        manager.stop()
