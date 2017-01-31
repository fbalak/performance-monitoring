from tendrl.node_monitoring import objects


class Node(objects.NodeMonitoringBaseObject):
    def __init__(self, fqdn=None,
                 status=None, *args, **kwargs):
        super(Node, self).__init__(*args, **kwargs)
        self.value = 'nodes/%s'
        self.list = 'nodes/'
        self.fqdn = fqdn
        self.status = status
        self._etcd_cls = None
