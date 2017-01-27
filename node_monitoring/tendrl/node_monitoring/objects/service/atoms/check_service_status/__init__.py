import os
from tendrl.node_monitoring.objects import NodeMonitoringBaseAtom
from tendrl.node_monitoring.objects.service import Service


class CheckServiceStatus(NodeMonitoringBaseAtom):
    obj = Service

    def run(self):
        service_name = self.parameters.get("Service.name")
        response = os.system("systemctl status %s" % service_name)
        # and then check the response...
        if response == 0:
            return True
        else:
            return False
