from tendrl.commons.atoms.base_atom import BaseAtom
from tendrl.commons.atoms.exceptions import AtomExecutionFailedError
from tendrl.commons.utils.command import Command


class Cmd(BaseAtom):
    def run(self, parameters):
        cmd = parameters.get("Node.cmd_str")
        out, err, rc = Command(cmd).run()
        if not err and rc == 0:
            return True
        else:
            raise AtomExecutionFailedError(err)
