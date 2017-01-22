import logging

from tendrl.performance_monitoring import objects
import uuid

LOG = logging.getLogger(__name__)


class TendrlContext(objects.PerformanceMonitoringBaseObject):
    def __init__(self, integration_id=None, node_id=None, *args, **kwargs):
        super(TendrlContext, self).__init__(*args, **kwargs)

        # integration_id is a random one time generated uuid and not cluster id
        # because this can be required even before a cluster is created.
        self.integration_id = integration_id or str(uuid.uuid4())
        self.node_id = node_id or str(uuid.uuid4())
        self._etcd_cls = None
        self.value = 'nodes/%s/TendrlContext' % self.node_id
