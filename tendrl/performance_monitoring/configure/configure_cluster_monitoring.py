from etcd import EtcdKeyNotFound
import gevent
import logging
import multiprocessing
from tendrl.performance_monitoring.sds import SDSMonitoringManager
from tendrl.performance_monitoring.utils import initiate_config_generation
import time


LOG = logging.getLogger(__name__)


class ConfigureClusterMonitoring(multiprocessing.Process):
    def __init__(self):
        super(ConfigureClusterMonitoring, self).__init__()
        self._complete = multiprocessing.Event()
        self.sds_monitoring_manager = SDSMonitoringManager()

    def get_cluster_ids(self):
        cluster_ids = []
        try:
            clusters = tendrl_ns.etcd_orm.client.read(
                '/clusters'
            )
            for cluster in clusters._children:
                key_contents = cluster['key'].split('/')
                if len(key_contents) == 3:
                    cluster_id = key_contents[2]
                    cluster_ids.append(cluster_id)
            return cluster_ids
        except EtcdKeyNotFound:
            return cluster_ids

    def configure_cluster_monitoring(self):
        while not self._complete.is_set():
            try:
                cluster_ids = self.get_cluster_ids()
                for cluster_id in cluster_ids:
                    configs = self.sds_monitoring_manager.configure_monitoring(
                        cluster_id
                    )
                    if configs:
                        for config in configs:
                            gevent.sleep(0.1)
                            gevent.spawn(initiate_config_generation, config)
            except Exception:
                pass
            time.sleep(10)

    def run(self):
        self.configure_cluster_monitoring()

    def stop(self):
        self._complete.set()
