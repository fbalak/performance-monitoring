from tendrl.commons import flows


class NodeMonitoringBaseFlow(flows.BaseFlow):
    def __init__(self, *args, **kwargs):
        super(NodeMonitoringBaseFlow, self).__init__(*args, **kwargs)
