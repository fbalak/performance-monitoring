from mock import MagicMock
import sys
sys.modules['tendrl.common.config'] = MagicMock()
sys.modules['tendrl.common.log'] = MagicMock()
from tendrl.performance_monitoring.time_series_db.manager \
    import config
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBManager
# from tendrl.performance_monitoring.time_series_db.dbplugins.graphite \
#    import GraphitePlugin
del sys.modules['tendrl.common.config']
del sys.modules['tendrl.common.log']


class TestTimeSeriesDbManager(object):
    #    def test_time_series_db_manager_sucess(self, monkeypatch):
    #        def mock_config_get(package, parameter):
    #            if parameter == "time_series_db":
    #                return 'graphite'
    #        monkeypatch.setattr(config, 'get', mock_config_get)
    #        time_series_db_manager = TimeSeriesDBManager()
    #        assert isinstance(time_series_db_manager.get_plugin(),
    #        	GraphitePlugin)

    def test_time_series_db_manager_failed(self, monkeypatch):
        def mock_config_get_non_existing_plugin(package, parameter):
            if parameter == "time_series_db":
                return 'rhq'
        monkeypatch.setattr(config, 'get', mock_config_get_non_existing_plugin)
        time_series_db_manager = TimeSeriesDBManager()
        assert time_series_db_manager.get_plugin() is None
