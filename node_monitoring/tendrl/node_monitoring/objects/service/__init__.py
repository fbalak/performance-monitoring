from tendrl.commons.utils import service_status
from tendrl.node_monitoring import objects


class Service(objects.NodeMonitoringBaseObject):
    def __init__(self, service, running=None, exists=None,
                 *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)
        service_detail = self._get_service_info(service)
        self.value = 'nodes/%s/Services/%s'
        self.list = 'nodes/%s/Services/'
        self.running = running or service_detail['running']
        self.service = service
        self.exists = exists or service_detail['exists']
        self._etcd_cls = None

    def get_service_info(self, service_name):
        service = service_status.ServiceStatus(
            service_name,
            tendrl_ns.config['tendrl_ansible_exec_file']
        )
        return {"exists": service.exists(), "running": service.status()}
