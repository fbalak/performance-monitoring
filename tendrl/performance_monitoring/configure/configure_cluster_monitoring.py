import gevent
from tendrl.performance_monitoring.utils import initiate_config_generation


class ConfigureClusterMonitoring(gevent.greenlet.Greenlet):
    def __init__(self):
        super(ConfigureClusterMonitoring, self).__init__()
        self._complete = gevent.event.Event()

    def get_cluster_ids(self):
        cluster_ids = []
        try:
            clusters = NS.etcd_orm.client.read(
                '/clusters'
            )
            for cluster in clusters.leaves:
                key_contents = cluster.key.split('/')
                if len(key_contents) == 3:
                    cluster_id = key_contents[2]
                    cluster_ids.append(cluster_id)
            return cluster_ids
        except Exception:
            return cluster_ids

    def configure_cluster_monitoring(self):
        while not self._complete.is_set():
            try:
                cluster_ids = self.get_cluster_ids()
                for cluster_id in cluster_ids:
                    configs = NS.sds_monitoring_manager.configure_monitoring(
                        cluster_id
                    )
                    if configs:
                        for config in configs:
                            gevent.sleep(0.1)
                            gevent.spawn(initiate_config_generation, config)
            except Exception:
                pass
            gevent.sleep(10)

    def _run(self):
        self.configure_cluster_monitoring()

    def stop(self):
        self._complete.set()
