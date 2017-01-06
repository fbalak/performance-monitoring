from etcd import EtcdKeyNotFound
import logging
import multiprocessing
import signal
from tendrl.common import log
from tendrl.common.config import ConfigNotFound
from tendrl.common.config import TendrlConfig
from tendrl.common.etcdobj.etcdobj import Server as etcd_server
from tendrl.performance_monitoring.aggregator.summary import Summarise
import tendrl.performance_monitoring.api.manager as api_manager
from tendrl.performance_monitoring.configure.configurator import Configurator
from tendrl.performance_monitoring.configure.configure_monitoring \
    import ConfigureMonitoring
import tendrl.performance_monitoring.defaults.manager as defaults_manager
from tendrl.performance_monitoring.definitions.performance_monitoring \
    import data as def_data
from tendrl.performance_monitoring.persistence.tendrl_definitions \
    import TendrlDefinitions
import time
import yaml


config = TendrlConfig()


LOG = logging.getLogger(__name__)


class TendrlPerformanceManager(object):

    def __init__(self):
        try:
            etcd_kwargs = {
                'port': int(config.get("common", "etcd_port")),
                'host': config.get("common", "etcd_connection")
            }
            self.etcd_server = etcd_server(etcd_kwargs=etcd_kwargs)
            self.api_manager = api_manager.APIManager()
            self.defaults_manager = defaults_manager.DefaultsManager()
            self.configurator_queue = multiprocessing.Queue()
            self.configure_monitoring = ConfigureMonitoring(
                self.configurator_queue
            )
            self.configurator = Configurator(
                self.configurator_queue
            )
            self.node_summariser = Summarise()
        except ConfigNotFound:
            raise

    def load_defs(self):
        defs_path = 'tendrl_definitions_node_agent/data'
        try:
            defs = yaml.load(self.etcd_server.client.read(
                defs_path).value.decode("utf-8"))
            perf_defs = yaml.load(def_data)
            for key in perf_defs:
                if key.startswith('namespace.'):
                    namespace = key
            defs[namespace] = perf_defs[namespace]
            self.etcd_server.save(
                TendrlDefinitions(
                    updated=str(time.time()),
                    data=yaml.safe_dump(defs)
                )
            )
        except EtcdKeyNotFound:
            self.etcd_server.save(
                TendrlDefinitions(
                    updated=str(time.time()),
                    data=def_data
                )
            )

    def start(self):
        self.load_defs()
        self.api_manager.start()
        self.configure_monitoring.start()
        self.configurator.start()
        self.node_summariser.start()

    def stop(self):
        self.configurator_queue.close()
        try:
            self.configurator.stop()
            self.api_manager.stop()
            self.configure_monitoring.stop()
            self.api_manager.terminate()
            self.configure_monitoring.terminate()
            self.node_summariser.stop()
        except Exception as e:
            LOG.error(
                'Caught KeyboardInterrupt %s' % str(e), exc_info=True)


def main():
    log.setup_logging(
        config.get('tendrl_performance', 'log_cfg_path'),
        config.get('tendrl_performance', 'log_level')
    )
    tendrl_perf_manager = TendrlPerformanceManager()

    def terminate(sig, frame):
        LOG.error("Signal handler: stopping", exc_info=True)
        tendrl_perf_manager.stop()

    signal.signal(signal.SIGINT, terminate)
    tendrl_perf_manager.start()


if __name__ == "__main__":
    main()
