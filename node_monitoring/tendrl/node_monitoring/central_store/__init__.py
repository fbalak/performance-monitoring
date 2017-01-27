import logging
from tendrl.commons import central_store


LOG = logging.getLogger(__name__)


class NodeMonitoringEtcdCentralStore(central_store.EtcdCentralStore):
    def __init__(self):
        super(NodeMonitoringEtcdCentralStore, self).__init__()

    def save_config(self, config):
        tendrl_ns.etcd_orm.save(config)

    def save_definition(self, definition):
        tendrl_ns.etcd_orm.save(definition)

    def save_tendrlcontext(self, tendrl_context):
        tendrl_ns.etcd_orm.save(tendrl_context)
