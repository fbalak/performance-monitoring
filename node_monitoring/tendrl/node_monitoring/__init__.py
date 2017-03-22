try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()

from tendrl.commons import TendrlNS


class NodeMonitoringNS(TendrlNS):
    def __init__(
        self,
        ns_name='node_monitoring',
        ns_src='tendrl.node_monitoring'
    ):
        # Create the "NS.performance_monitoring" namespace
        super(NodeMonitoringNS, self).__init__(ns_name, ns_src)
