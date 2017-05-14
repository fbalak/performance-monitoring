from tendrl.commons import objects


class NodeSummary(objects.BaseObject):
    def __init__(
        self,
        name=None,
        node_id=None,
        status=None,
        role=None,
        cluster_name=None,
        cpu_usage=None,
        memory_usage=None,
        storage_usage=None,
        swap_usage=None,
        alert_count=None,
        sds_det=None,
        selinux_mode='',
        *args,
        **kwargs
    ):
        super(NodeSummary, self).__init__(*args, **kwargs)
        self.node_id = node_id
        if cpu_usage is not None:
            self.cpu_usage = cpu_usage
        if memory_usage is not None:
            self.memory_usage = memory_usage
        if storage_usage is not None:
            self.storage_usage = storage_usage
        if swap_usage is not None:
            self.swap_usage = swap_usage
        self.name = name
        self.status = status
        self.role = role
        self.cluster_name = cluster_name
        self.selinux_mode = selinux_mode
        self.sds_det = sds_det
        self.alert_count = alert_count
        self.value = 'monitoring/summary/nodes/{0}'

    def to_json(self):
        # TODO (anmolB) use self.json instead of this method
        return self.__dict__

    def render(self):
        self.value = self.value.format(self.node_id)
        return super(NodeSummary, self).render()
