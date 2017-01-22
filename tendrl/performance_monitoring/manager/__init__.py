import logging
import multiprocessing
import os
import signal
from tendrl.commons.config import ConfigNotFound
from tendrl.performance_monitoring.aggregator.summary import Summarise
import tendrl.performance_monitoring.api.manager as api_manager
from tendrl.performance_monitoring.central_store \
    import PerformanceMonitoringEtcdCentralStore
from tendrl.performance_monitoring.configure.configurator import Configurator
from tendrl.performance_monitoring.configure.configure_monitoring \
    import ConfigureMonitoring
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.objects.config import Config
from tendrl.performance_monitoring.objects.definition import Definition
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBManager
from tendrl.commons.log import setup_logging


LOG = logging.getLogger(__name__)


class TendrlPerformanceManager(object):

    def __init__(self):
        try:
            api_server = tendrl_ns.config.data[
                'api_server_addr'
            ]
            api_port = tendrl_ns.config.data[
                'api_server_port'
            ]
            t_manager = TimeSeriesDBManager(
                tendrl_ns.config.data
            )
            self.api_manager = api_manager.APIManager(
                api_server,
                api_port,
                t_manager
            )
            tendrl_ns.configurator_queue = multiprocessing.Queue()
            self.configure_monitoring = ConfigureMonitoring()
            self.configurator = Configurator()
            self.node_summariser = Summarise(t_manager)
        except (ConfigNotFound, TendrlPerformanceMonitoringException):
            raise

    def start(self):
        self.api_manager.start()
        self.configure_monitoring.start()
        self.configurator.start()
        self.node_summariser.start()

    def stop(self):
        tendrl_ns.configurator_queue.close()
        self.api_manager.stop()
        self.node_summariser.stop()
        self.api_manager.terminate()
        os.system("ps -C tendrl-performance-monitoring -o pid=|xargs kill -9")


def main():
    tendrl_ns.central_store_thread = PerformanceMonitoringEtcdCentralStore()
    tendrl_ns.monitoring_config_init_nodes = []
    tendrl_ns.definitions.save()
    tendrl_ns.config.save()

    tendrl_perf_manager = TendrlPerformanceManager()

    def terminate(sig, frame):
        LOG.error("Signal handler: stopping", exc_info=True)
        tendrl_perf_manager.stop()

    signal.signal(signal.SIGINT, terminate)
    tendrl_perf_manager.start()


if __name__ == "__main__":
    main()
