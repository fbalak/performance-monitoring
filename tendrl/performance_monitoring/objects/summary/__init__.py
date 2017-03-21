import logging
from tendrl.commons.etcdobj import EtcdObj
from tendrl.commons.objects import BaseObject


LOG = logging.getLogger(__name__)


class PerformanceMonitoringSummary(BaseObject):
    def __init__(self,
                 node_id=None,
                 cpu_usage=None,
                 memory_usage=None,
                 storage_usage=None,
                 alert_count=None,
                 *args,
                 **kwargs
                 ):
        super(PerformanceMonitoringSummary, self).__init__(*args, **kwargs)
        self.node_id = node_id
        self.value = 'monitoring/summary/nodes/%s' % self.node_id
        self._etcd_cls = _PerformanceMonitoringSummary
        if cpu_usage is not None:
            self.cpu_usage = cpu_usage
        if memory_usage is not None:
            self.memory_usage = memory_usage
        if storage_usage is not None:
            self.storage_usage = storage_usage
        self.alert_count = alert_count

    def to_json(self):
        return self.__dict__


class _PerformanceMonitoringSummary(EtcdObj):
    """A table of the node context, lazily updated

    """
    __name__ = 'monitoring/summary/nodes/%s'
    _tendrl_cls = PerformanceMonitoringSummary

    def render(self):
        self.__name__ = self.__name__ % self.node_id
        return super(_PerformanceMonitoringSummary, self).render()
