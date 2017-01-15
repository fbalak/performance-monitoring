import logging
import multiprocessing
import signal
from tendrl.commons import log
from tendrl.commons.config import ConfigNotFound
from tendrl.commons.config import TendrlConfig
from tendrl.performance_monitoring.aggregator.summary import Summarise
import tendrl.performance_monitoring.api.manager as api_manager
from tendrl.performance_monitoring.configure.configurator import Configurator
from tendrl.performance_monitoring.configure.configure_monitoring \
    import ConfigureMonitoring
import tendrl.performance_monitoring.defaults.manager as defaults_manager
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.persistence.persister \
    import PerformanceMonitoringEtcdPersister
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBManager


config = TendrlConfig('tendrl_performance', '/etc/tendrl/tendrl.conf')


LOG = logging.getLogger(__name__)


class TendrlPerformanceManager(object):

    def __init__(self):
        try:
            self.persister = PerformanceMonitoringEtcdPersister(config)
            api_server = config.get(
                "tendrl_performance",
                "api_server_addr"
            )
            api_port = config.get(
                "tendrl_performance",
                "api_server_port"
            )
            t_manager = TimeSeriesDBManager(
                config,
                config.get('time_series', 'time_series_db')
            )
            self.api_manager = api_manager.APIManager(
                api_server,
                api_port,
                self.persister,
                t_manager
            )
            self.defaults_manager = defaults_manager.DefaultsManager(
                self.persister,
                api_server,
                api_port
            )
            self.configurator_queue = multiprocessing.Queue()
            self.configure_monitoring = ConfigureMonitoring(
                self.configurator_queue,
                PerformanceMonitoringEtcdPersister(config)
            )
            self.configurator = Configurator(
                self.configurator_queue,
                self.persister
            )
            self.node_summariser = Summarise(self.persister, t_manager)
        except (ConfigNotFound, TendrlPerformanceMonitoringException):
            raise

    def start(self):
        self.persister.update_defs()
        self.api_manager.start()
        self.configure_monitoring.start()
        self.configurator.start()
        self.node_summariser.start()

    def stop(self):
        self.configurator_queue.close()
        try:
            self.configurator.stop()
            self.api_manager.stop()
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

