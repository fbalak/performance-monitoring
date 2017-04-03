from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons.objects import BaseObject


class SystemSummary(BaseObject):
    def __init__(self,
                 cluster_count={},
                 utilization={},
                 hosts_count={},
                 sds_det={},
                 sds_type='',
                 *args,
                 **kwargs
                 ):
        super(
            SystemSummary,
            self
        ).__init__(*args, **kwargs)
        self.utilization = utilization
        self.cluster_count = cluster_count
        self.hosts_count = hosts_count
        self.sds_det = sds_det
        self.sds_type = sds_type
        self.value = 'monitoring/summary/system/%s' % self.sds_type
        self._etcd_cls = _SystemSummaryEtcd

    def to_json(self):
        return self.__dict__


class _SystemSummaryEtcd(EtcdObj):
    """A table of the node context, lazily updated

    """
    __name__ = 'monitoring/summary/system/%s'
    _tendrl_cls = SystemSummary

    def render(self):
        self.__name__ = self.__name__ % self.sds_type
        return super(_SystemSummaryEtcd, self).render()
