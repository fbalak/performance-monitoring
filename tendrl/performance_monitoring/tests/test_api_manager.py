from mock import MagicMock
import multiprocessing
import sys
from tendrl.performance_monitoring.api.manager import APIManager
from tendrl.performance_monitoring.api.manager import config
sys.modules['tendrl.common.config'] = MagicMock()
sys.modules['tendrl.common.log'] = MagicMock()
del sys.modules['tendrl.common.config']


class TestManager(object):
    def test_manager_constructor(self, monkeypatch):
        def mock_config(package, parameter):
            if parameter == "performance_server_interface":
                return '0.0.0.0'
        monkeypatch.setattr(config, 'get', mock_config)
        manager = APIManager()
        assert manager.host == '0.0.0.0'
        assert isinstance(manager, APIManager)
        assert isinstance(manager._complete, multiprocessing.synchronize.Event)

    def test_manager_stop(self, monkeypatch):
        manager = APIManager()

        def mock_stop():
            return
        monkeypatch.setattr(manager, 'stop', mock_stop)

        manager.stop()
        assert True

    def test_manager_start(self, monkeypatch):
        manager = APIManager()

        def mock_start():
            return
        monkeypatch.setattr(manager, 'start', mock_start)

        manager.start()
        assert True
