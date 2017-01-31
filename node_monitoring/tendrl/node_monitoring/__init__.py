try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()

from tendrl.commons import etcdobj
from tendrl.commons import log
from tendrl.commons import CommonNS

from tendrl.node_monitoring.flows.configure_collectd \
    import ConfigureCollectd

from tendrl.node_monitoring.objects.config import Config
from tendrl.node_monitoring.objects.definition import Definition
from tendrl.node_monitoring.objects.node import Node
from tendrl.node_monitoring.objects.node_context import NodeContext
from tendrl.node_monitoring.objects.tendrl_context import TendrlContext
from tendrl.node_monitoring.objects.service import Service

from tendrl.node_monitoring.objects.node.atoms.check_node_up import CheckNodeUp
from tendrl.node_monitoring.objects.node.atoms.cmd import Cmd
from tendrl.node_monitoring.objects.service.atoms.check_service_status \
    import CheckServiceStatus


class NodeMonitoringNS(CommonNS):
    def __init__(self):

        # Create the "tendrl_ns.performance_monitoring" namespace
        self.to_str = "tendrl.node_monitoring"
        self.type = 'monitoring'
        super(NodeMonitoringNS, self).__init__()


NodeMonitoringNS()
