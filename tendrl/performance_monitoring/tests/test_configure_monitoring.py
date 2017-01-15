from ConfigParser import SafeConfigParser
from etcd import client
from etcd import EtcdResult
from mock import MagicMock
import multiprocessing
import sys
sys.modules['tendrl.common.config'] = MagicMock()
sys.modules['tendrl.common.log'] = MagicMock()
from tendrl.performance_monitoring.configure.configure_monitoring \
    import ConfigureMonitoring
from tendrl.performance_monitoring.persistence.persister \
    import PerformanceMonitoringEtcdPersister
del sys.modules['tendrl.common.config']
del sys.modules['tendrl.common.log']


class TestConfigureMonitoring(object):
    def get_persister(self):
        cParser = SafeConfigParser()
        cParser.add_section('commons')
        cParser.set('commons', 'etcd_connection', '0.0.0.0')
        cParser.set('commons', 'etcd_port', '2379')
        return PerformanceMonitoringEtcdPersister(cParser)

    def test_configure_monitoring_constructor(self, monkeypatch):
        persister = self.get_persister()

        def mock_get_node_dets():
            return [
                {
                    'node_id': '083b7911-194c-411e-9cfb-83ce6c4e6928',
                    'fqdn': 'test.configure_monitoring.com'
                }
            ]

        monkeypatch.setattr(
            persister,
            'get_nodes_details',
            mock_get_node_dets
        )
        configure_monitoring = ConfigureMonitoring(
            multiprocessing.Queue(),
            persister
        )
        assert isinstance(
            configure_monitoring.persister,
            PerformanceMonitoringEtcdPersister
        )
        assert isinstance(configure_monitoring.configurator_queue,
                          multiprocessing.queues.Queue)
        expected_node_det = {
            'node_id': '083b7911-194c-411e-9cfb-83ce6c4e6928',
            'fqdn': 'test.configure_monitoring.com'
        }

        def mock_queue_put(node_det):
            assert node_det == expected_node_det

        monkeypatch.setattr(
            configure_monitoring.configurator_queue,
            'put',
            mock_queue_put
        )
        configure_monitoring.init_monitoring()

    def test_configure_monitoring_start(self, monkeypatch):
        persister = self.get_persister()

        def mock_get_node_dets():
            return [
                {
                    'node_id': '083b7911-194c-411e-9cfb-83ce6c4e6928',
                    'fqdn': 'test.configure_monitoring.com'
                }
            ]

        monkeypatch.setattr(
            persister,
            'get_nodes_details',
            mock_get_node_dets
        )

        def mock_watch_nodes():
            return

        configure_monitoring = ConfigureMonitoring(
            multiprocessing.Queue(),
            persister
        )
        monkeypatch.setattr(
            configure_monitoring,
            'watch_nodes',
            mock_watch_nodes
        )
        configure_monitoring.run()
        assert True
