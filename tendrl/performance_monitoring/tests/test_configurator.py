import etcd
import json
from mock import MagicMock
import multiprocessing
import pytest
import sys
sys.modules['tendrl.common.config'] = MagicMock()
sys.modules['tendrl.common.log'] = MagicMock()
from tendrl.performance_monitoring.configure.configurator import config
from tendrl.performance_monitoring.configure.configurator import Configurator
del sys.modules['tendrl.common.config']
del sys.modules['tendrl.common.log']


class TestConfigurator(object):
    def test_configurator_constructor(self, monkeypatch):
        def mock_config(package, parameter):
            if parameter == "etcd_port":
                return '0'
            elif parameter == "etcd_connection":
                return '0.0.0.0'
        monkeypatch.setattr(config, 'get', mock_config)
        configurator = Configurator(multiprocessing.Queue())
        assert isinstance(configurator.configurator_queue,
                          multiprocessing.queues.Queue)
        assert isinstance(configurator._complete,
                          multiprocessing.synchronize.Event)
        assert isinstance(configurator.etcd_client, etcd.client.Client)

    def test_configurator_run(self, monkeypatch):
        def mock_config(package, parameter):
            if parameter == "etcd_port":
                return '0'
            elif parameter == "etcd_connection":
                return '0.0.0.0'
        monkeypatch.setattr(config, 'get', mock_config)
        configurator = Configurator(multiprocessing.Queue())

        def mock_monitoring_config():
            return {
                'interval': 60,
                'thresholds': {
                    'cpu': {'Warning': 80, 'Failure': 90},
                    'mount_point': {'Warning': 80, 'Failure': 90},
                    'memory': {'Warning': 80, 'Failure': 90},
                    'swap': {'Warning': 50, 'Failure': 70}
                }
            }
        monkeypatch.setattr(configurator, 'get_configs',
                            mock_monitoring_config)

        def mock_etcd_write(k, val,
                            ttl=None, dir=False, append=False, **kwdargs):
            expected_val = {
                'node_id': '11927f2f-39ec-450d-bf19-b2b00a53c394',
                "run": 'tendrl.node_monitoring.flows.configure_collectd.\
                ConfigureCollectd',
                'status': 'new',
                'type': 'node',
                "parameters": {
                    'plugin_name': 'cpu',
                    'plugin_conf_params': "{\"Failure\": 90, \"Warning\": 80}",
                    'Node.fqdn': 'test.configurator.com',
                    'service_name': 'collectd'
                }
            }
            assert val == json.dumps(expected_val)
        monkeypatch.setattr(configurator.etcd_client, 'write', mock_etcd_write)
        node_det = {'node_id': '11927f2f-39ec-450d-bf19-b2b00a53c394',
                    'fqdn': 'test.configurator.com'}
        cpu_conf = mock_monitoring_config()['thresholds']['cpu']
        configurator.initiate_config_generation('cpu', cpu_conf, node_det)

        def mock_run():
            pass

        monkeypatch.setattr(configurator, 'start', mock_run)
        configurator.start()

    def test_configurator_run_failure(self, monkeypatch):
        def mock_config(package, parameter):
            if parameter == "etcd_port":
                return '0'
            elif parameter == "etcd_connection":
                return '0.0.0.0'
        monkeypatch.setattr(config, 'get', mock_config)
        configurator = Configurator(multiprocessing.Queue())

        def mock_monitoring_config():
            return {
                'interval': 60,
                'thresholds': {
                    'cpu': {'Warning': 80, 'Failure': 90},
                    'mount_point': {'Warning': 80, 'Failure': 90},
                    'memory': {'Warning': 80, 'Failure': 90},
                    'swap': {'Warning': 50, 'Failure': 70}
                }
            }
        monkeypatch.setattr(configurator, 'get_configs',
                            mock_monitoring_config)

        node_det = {'node_id': '11927f2f-39ec-450d-bf19-b2b00a53c394',
                    'fqdn': 'test.configurator.com'}
        pytest.raises(etcd.EtcdException,
                      configurator.initiate_config_generation,
                      'cpu',
                      mock_monitoring_config()['thresholds']['cpu'],
                      node_det
                      )
