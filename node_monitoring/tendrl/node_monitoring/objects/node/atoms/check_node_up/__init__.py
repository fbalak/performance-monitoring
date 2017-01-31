import os

from tendrl.node_monitoring.objects import NodeMonitoringBaseAtom
from tendrl.node_monitoring.objects.node import Node


class CheckNodeUp(NodeMonitoringBaseAtom):

    obj = Node

    def run(self):
        fqdn = self.parameters.get("fqdn")
        response = os.system("ping -c 1 " + fqdn)
        # and then check the response...
        if response == 0:
            return True
        else:
            return False
