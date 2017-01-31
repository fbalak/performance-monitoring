from tendrl.commons.objects.atoms import AtomExecutionFailedError
from tendrl.commons.utils.cmd_utils import Command
from tendrl.node_monitoring.objects import NodeMonitoringBaseAtom
from tendrl.node_monitoring.objects.node import Node


class Cmd(NodeMonitoringBaseAtom):
    obj = Node

    def run(self):
        cmd = self.parameters.get("Node.cmd_str")
        out, err, rc = Command(cmd).run(
            tendrl_ns.config.data['tendrl_ansible_exec_file']
        )
        if not err and rc == 0:
            return True
        else:
            raise AtomExecutionFailedError(err)
