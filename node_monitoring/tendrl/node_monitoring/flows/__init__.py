import logging

from tendrl.commons import flows

LOG = logging.getLogger(__name__)


class NodeMonitoringBaseFlow(flows.BaseFlow):
    def __init__(self, *args, **kwargs):
        super(NodeMonitoringBaseFlow, self).__init__(*args, **kwargs)
