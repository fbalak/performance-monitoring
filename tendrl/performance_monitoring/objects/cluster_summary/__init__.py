import json
from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons.objects import BaseObject


class ClusterSummary(BaseObject):
    def __init__(self,
                 utilization={'': ''},
                 hosts_count={'': ''},
                 node_summaries=[],
                 sds_det={'': ''},
                 sds_type='',
                 cluster_id='',
                 *args,
                 **kwargs
                 ):
        super(
            ClusterSummary,
            self
        ).__init__(*args, **kwargs)
        self.cluster_id = cluster_id
        self.utilization = utilization
        self.hosts_count = hosts_count
        self.node_summaries = node_summaries
        self.sds_det = sds_det
        self.sds_type = sds_type
        self.value = 'monitoring/summary/clusters/%s' % self.cluster_id
        self._etcd_cls = _ClusterSummaryEtcd

    def to_json(self):
        return self.__dict__

    def save(self, update=False):
        # Convert nested dict to str @ save and convert back to
        # dict on load
        self.node_summaries = json.dumps(self.node_summaries)
        self.hosts_count = json.dumps(self.hosts_count)
        self.utilization = json.dumps(self.utilization)
        self.sds_det = json.dumps(self.sds_det)
        super(ClusterSummary, self).save(update=update)

    def load(self):
        summary = super(ClusterSummary, self).load()
        if isinstance(summary.node_summaries, basestring):
            summary.node_summaries = json.loads(summary.node_summaries)
        summary.sds_det = json.loads(summary.sds_det[''])
        summary.hosts_count = json.loads(self.hosts_count[''])
        summary.utilization = json.loads(self.utilization[''])
        return summary

    def copy(self):
        return ClusterSummary(
            utilization=self.utilization,
            hosts_count=self.hosts_count,
            node_summaries=self.node_summaries,
            sds_det=self.sds_det,
            sds_type=self.sds_type,
            cluster_id=self.cluster_id
        )


class _ClusterSummaryEtcd(EtcdObj):
    """A table of the node context, lazily updated

    """
    __name__ = 'monitoring/summary/clusters/%s'
    _tendrl_cls = ClusterSummary

    def render(self):
        self.__name__ = self.__name__ % self.cluster_id
        return super(_ClusterSummaryEtcd, self).render()
