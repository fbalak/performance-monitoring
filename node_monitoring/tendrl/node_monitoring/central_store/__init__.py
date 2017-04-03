from tendrl.commons import central_store


class NodeMonitoringEtcdCentralStore(central_store.EtcdCentralStore):
    def __init__(self):
        super(NodeMonitoringEtcdCentralStore, self).__init__()

    def save_config(self, config):
        NS.etcd_orm.save(config)

    def save_definition(self, definition):
        NS.etcd_orm.save(definition)
