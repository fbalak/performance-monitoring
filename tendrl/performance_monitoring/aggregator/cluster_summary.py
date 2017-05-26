from etcd import EtcdKeyNotFound
import gevent
from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.performance_monitoring.objects.cluster_summary \
    import ClusterSummary
import tendrl.performance_monitoring.utils.central_store_util \
    as central_store_util


class ClusterSummarise(gevent.greenlet.Greenlet):
    def __init__(self):
        super(ClusterSummarise, self).__init__()
        self._complete = gevent.event.Event()

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
            alerts = []
            try:
                alerts = central_store_util.get_node_alerts(node_id)
            except EtcdKeyNotFound:
                pass
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
        try:
            for node_id in node_ids:
                node_summary = central_store_util.read(
                    '/monitoring/summary/nodes/%s' % node_id
                )
                node_summaries.append(node_summary)
        except EtcdKeyNotFound:
            return node_summaries
        return node_summaries

    def parse_cluster(self, cluster_id, cluster_det):
        utilization = cluster_det.get('Utilization', {})
        used = 0
        total = 0
        percent_used = 0
        if utilization.get('used_capacity'):
            used = utilization.get('used_capacity')
        elif utilization.get('used'):
            used = utilization.get('used')
        if utilization.get('raw_capacity'):
            total = utilization.get('raw_capacity')
        elif utilization.get('total'):
            total = utilization.get('total')
        if utilization.get('pcnt_used'):
            percent_used = utilization.get('pcnt_used')
        return ClusterSummary(
            utilization={
                'total': int(total),
                'used': int(used),
                'percent_used': float(percent_used)
            },
            hosts_count=self.parse_host_count(cluster_det.get('nodes', {})),
            sds_type=cluster_det.get('TendrlContext', {}).get('sds_name'),
            node_summaries=self.cluster_nodes_summary(
                cluster_det.get('nodes', {}).keys()
            ),
            sds_det=NS.sds_monitoring_manager.get_cluster_summary(
                cluster_id,
                cluster_det
            ),
            cluster_id=cluster_id,
        )

    def _run(self):
        while not self._complete.is_set():
            cluster_summaries = []
            try:
                clusters = central_store_util.read('/clusters')
                for clusterid, cluster_det in clusters.iteritems():
                    gevent.sleep(0.1)
                    cluster_summary = self.parse_cluster(clusterid,
                                                         cluster_det)
                    cluster_summaries.append(cluster_summary.copy())
                    cluster_summary.save(update=False)
                NS.sds_monitoring_manager.compute_system_summary(
                    cluster_summaries,
                    clusters
                )
            except EtcdKeyNotFound:
                pass
            except Exception as ex:
                Event(
                    ExceptionMessage(
                        priority="error",
                        publisher=NS.publisher_id,
                        payload={
                            "message": 'Error caught computing summary.',
                            "exception": ex
                            }
                    )
                )
            gevent.sleep(60)

    def stop(self):
        self._complete.set()
