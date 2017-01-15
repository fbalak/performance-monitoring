from ConfigParser import SafeConfigParser
import json
from mock import MagicMock
import multiprocessing
import sys
sys.modules['tendrl.common.config'] = MagicMock()
sys.modules['tendrl.common.log'] = MagicMock()
from tendrl.performance_monitoring.configure.configurator import Configurator
from tendrl.performance_monitoring.persistence.persister \
    import PerformanceMonitoringEtcdPersister
del sys.modules['tendrl.common.config']
del sys.modules['tendrl.common.log']


class TestConfigurator(object):
    def get_persister(self):
        cParser = SafeConfigParser()
        cParser.add_section('commons')
        cParser.set('commons', 'etcd_connection', '0.0.0.0')
        cParser.set('commons', 'etcd_port', '2379')
        return PerformanceMonitoringEtcdPersister(cParser)

    def test_configurator_constructor(self, monkeypatch):
        configurator = Configurator(
            multiprocessing.Queue(),
            self.get_persister()
        )
        assert isinstance(configurator.configurator_queue,
                          multiprocessing.queues.Queue)
        assert isinstance(configurator._complete,
                          multiprocessing.synchronize.Event)
        assert isinstance(
            configurator.persister,
            PerformanceMonitoringEtcdPersister
        )

    def test_configurator_run(self, monkeypatch):
        persister = self.get_persister()
        configurator = Configurator(
            multiprocessing.Queue(),
            persister
        )

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
        monkeypatch.setattr(configurator.persister, 'get_configs',
                            mock_monitoring_config)

        def mock_etcd_write(k, val,
                            ttl=None, dir=False, append=False, **kwdargs):
            expected_val = {
                'node_id': '11927f2f-39ec-450d-bf19-b2b00a53c394',
                "run": 'tendrl.node_monitoring.flows.configure_collectd.'
                'ConfigureCollectd',
                'status': 'new',
                'type': 'node',
                "parameters": {
                    'plugin_name': 'cpu',
                    'plugin_conf_params': "{\"Failure\": 90, \"Warning\": 80}",
                    'Node.fqdn': 'test.configurator.com',
                    'Service.name': 'collectd'
                }
            }
            assert val == json.dumps(expected_val)
        monkeypatch.setattr(
            persister._store.client,
            'write',
            mock_etcd_write
        )
        node_det = {'node_id': '11927f2f-39ec-450d-bf19-b2b00a53c394',
                    'fqdn': 'test.configurator.com'}
        cpu_conf = mock_monitoring_config()['thresholds']['cpu']
        configurator.initiate_config_generation('cpu', cpu_conf, node_det)

        def mock_run():
            pass

        monkeypatch.setattr(configurator, 'start', mock_run)
        configurator.start()
