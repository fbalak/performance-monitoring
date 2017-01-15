from ConfigParser import SafeConfigParser
from mock import MagicMock
import multiprocessing
import sys
from tendrl.performance_monitoring.api.manager import APIManager
from tendrl.performance_monitoring.persistence.persister \
    import PerformanceMonitoringEtcdPersister
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBManager
sys.modules['tendrl.common.config'] = MagicMock()
sys.modules['tendrl.common.log'] = MagicMock()
del sys.modules['tendrl.common.config']


class TestManager(object):

    def get_persister(self):
        cParser = SafeConfigParser()
        cParser.add_section('commons')
        cParser.set('commons', 'etcd_connection', '0.0.0.0')
        cParser.set('commons', 'etcd_port', '2379')
        return PerformanceMonitoringEtcdPersister(cParser)

    def get_time_series_db_manager(self):
        cParser = SafeConfigParser()
        cParser.add_section('commons')
        cParser.set('commons', 'etcd_connection', '0.0.0.0')
        cParser.set('commons', 'etcd_port', '2379')
        cParser.add_section('time_series')
        cParser.set('time_series', 'time_series_db_server', '0.0.0.0')
        cParser.set('time_series', 'time_series_db_port', '80')
        return TimeSeriesDBManager(cParser, 'graphite')

    def test_manager_constructor(self, monkeypatch):
        manager = APIManager(
            '0.0.0.0',
            '5000',
            self.get_persister(),
            self.get_time_series_db_manager()
        )
        assert manager.host == '0.0.0.0'
        assert isinstance(manager, APIManager)
        assert isinstance(manager._complete, multiprocessing.synchronize.Event)

    def test_manager_stop(self, monkeypatch):
        manager = APIManager(
            '0.0.0.0',
            '5000',
            self.get_persister(),
            self.get_time_series_db_manager()
        )

        def mock_stop():
            return
        monkeypatch.setattr(manager, 'stop', mock_stop)

        manager.stop()
        assert True

    def test_manager_start(self, monkeypatch):
        manager = APIManager(
            '0.0.0.0',
            '5000',
            self.get_persister(),
            self.get_time_series_db_manager()
        )

        def mock_start():
            return
        monkeypatch.setattr(manager, 'start', mock_start)

        manager.start()
        assert True
