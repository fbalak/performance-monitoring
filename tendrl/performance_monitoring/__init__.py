try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()

from tendrl.commons import etcdobj
from tendrl.commons import log
from tendrl.commons import CommonNS

from tendrl.performance_monitoring.objects.config import Config
from tendrl.performance_monitoring.objects.definition import Definition
from tendrl.performance_monitoring.objects.node_context import NodeContext
from tendrl.performance_monitoring.objects.summary import PerformanceMonitoringSummary
from tendrl.performance_monitoring.objects.tendrl_context import TendrlContext


class PerformanceMonitoringNS(CommonNS):
    def __init__(self):

        # Create the "tendrl_ns.performance_monitoring" namespace
        self.to_str = "tendrl.performance_monitoring"
        super(PerformanceMonitoringNS, self).__init__()


PerformanceMonitoringNS()
