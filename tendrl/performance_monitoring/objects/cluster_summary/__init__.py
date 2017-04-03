from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons.objects import BaseObject


class ClusterSummary(BaseObject):
    def __init__(self,
                 utilization={},
                 hosts_count={},
                 node_summaries=[],
                 sds_det={},
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


class _ClusterSummaryEtcd(EtcdObj):
    """A table of the node context, lazily updated

    """
    __name__ = 'monitoring/summary/clusters/%s'
    _tendrl_cls = ClusterSummary

    def render(self):
        self.__name__ = self.__name__ % self.cluster_id
        return super(_ClusterSummaryEtcd, self).render()
