import multiprocessing
from tendrl.commons.utils.etcd_util import read as etcd_read
from tendrl.performance_monitoring.objects.cluster_summary \
    import ClusterSummary
from tendrl.performance_monitoring.sds import SDSMonitoringManager
import time


class ClusterSummarise(multiprocessing.Process):
    def __init__(self):
        super(ClusterSummarise, self).__init__()
        self._complete = multiprocessing.Event()
        self.sds_monitoring_manager = SDSMonitoringManager()

    def parse_host_count(self, cluster_nodes):
        status_wise_count = {
            'total': 0,
            'down': 0,
            'crit_alert_count': 0,
            'warn_alert_count': 0
        }
        for node_id, node_det in cluster_nodes.iteritems():
            status = node_det.get('NodeContext', {}).get('status')
            if status:
                if status != 'UP':
                    status_wise_count['down'] = status_wise_count['down'] + 1
            status_wise_count['total'] = status_wise_count['total'] + 1
            alerts = NS.central_store_thread.get_node_alerts(node_id)
            for alert in alerts:
                if alert.get('severity') == 'CRITICAL':
                    status_wise_count['crit_alert_count'] = \
                        status_wise_count['crit_alert_count'] + 1
                elif alert.get('severity') == 'WARNING':
                    status_wise_count['warn_alert_count'] = \
                        status_wise_count['warn_alert_count'] + 1
        return status_wise_count

    def cluster_nodes_summary(self, node_ids):
        node_summaries = []
        for node_id in node_ids:
            node_summary = etcd_read('/monitoring/summary/nodes/%s' % node_id)
            node_summaries.append(node_summary)
        return node_summaries

    def parse_cluster(self, cluster_id, cluster_det):
        return ClusterSummary(
            utilization={
                'total': cluster_det.get(
                    'Utilization', {}
                ).get('raw_capacity') or
                cluster_det.get(
                    'Utilization', {}
                ).get('total'),
                'used': cluster_det.get(
                    'Utilization', {}
                ).get('used_capacity'),
                'percent_used': cluster_det.get(
                    'Utilization', {}
                ).get('pcnt_used'),
            },
            sds_det=self.sds_monitoring_manager.get_cluster_summary(
                cluster_id,
                cluster_det
            ),
            hosts_count=self.parse_host_count(cluster_det.get('nodes')),
            sds_type=cluster_det.get('TendrlContext', {}).get('sds_name'),
            node_summaries=self.cluster_nodes_summary(
                cluster_det.get('nodes', {}).keys()
            ),
            cluster_id=cluster_id,
        )

    def run(self):
        while not self._complete.is_set():
            cluster_summaries = []
            clusters = etcd_read('/clusters')
            for clusterid, cluster_det in clusters.iteritems():
                cluster_summary = self.parse_cluster(clusterid, cluster_det)
                cluster_summary.save()
                cluster_summaries.append(cluster_summary)
            self.sds_monitoring_manager.compute_system_summary(
                cluster_summaries,
                clusters
            )
            time.sleep(60)

    def stop(self):
        self._complete.set()
