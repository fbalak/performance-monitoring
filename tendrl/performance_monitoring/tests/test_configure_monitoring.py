from etcd import client
from etcd import EtcdResult
from mock import MagicMock
import multiprocessing
import sys
sys.modules['tendrl.common.config'] = MagicMock()
sys.modules['tendrl.common.log'] = MagicMock()
from tendrl.performance_monitoring.configure.configure_monitoring \
    import config
from tendrl.performance_monitoring.configure.configure_monitoring \
    import ConfigureMonitoring
del sys.modules['tendrl.common.config']
del sys.modules['tendrl.common.log']


class TestConfigureMonitoring(object):
    def test_configure_monitoring_constructor(self, monkeypatch):
        def mock_config(package, parameter):
            if parameter == "etcd_port":
                return '0'
            elif parameter == "etcd_connection":
                return '0.0.0.0'
        monkeypatch.setattr(config, 'get', mock_config)

        def mock_etcd_read(key, **kwdargs):
            if key == '/nodes/':
                node_id_dict = {
                    'key': '/nodes/083b7911-194c-411e-9cfb-83ce6c4e6928',
                    'dir': True
                }
                nodes_dict = {
                    'node': {
                        'key': '/nodes',
                        'nodes': [node_id_dict],
                        'dir': True
                    }
                }
                return EtcdResult(**nodes_dict)
            elif key == '/nodes/083b7911-194c-411e-9cfb-83ce6c4e6928/\
            Node_context/fqdn':
                return {
                    'value': 'test.configure_monitoring.com',
                    'key': '/nodes/083b7911-194c-411e-9cfb-83ce6c4e6928/\
                    Node_context/fqdn'
                }

        configure_monitoring = ConfigureMonitoring(multiprocessing.Queue())
        monkeypatch.setattr(
            configure_monitoring.etcd_client,
            'read',
            mock_etcd_read
        )
        assert isinstance(configure_monitoring.etcd_client, client.Client)
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
        def mock_config(package, parameter):
            if parameter == "etcd_port":
                return '0'
            elif parameter == "etcd_connection":
                return '0.0.0.0'

        monkeypatch.setattr(config, 'get', mock_config)
        configure_monitoring = ConfigureMonitoring(multiprocessing.Queue())

        def mock_watch_nodes():
            return

        monkeypatch.setattr(
            configure_monitoring,
            'watch_nodes',
            mock_watch_nodes
        )
        assert True
