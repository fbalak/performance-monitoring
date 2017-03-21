import socket
from tendrl.commons.event import Event
from tendrl.commons.flows import BaseFlow
from tendrl.commons.message import Message


class ConfigureCollectd(BaseFlow):

    def run(self):
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={
                    "message": "Starting configuration of %s on %s with %s as"
                    " conf parameters" % (
                        self.parameters['plugin_name'],
                        socket.getfqdn(),
                        self.parameters['plugin_conf_params']
                    )
                },
                job_id=self.parameters['job_id'],
                flow_id=self.parameters['flow_id'],
            )
        )
        self.parameters['Node.cmd_str'] = "config_manager %s '%s'" % (
            self.parameters['plugin_name'],
            self.parameters['plugin_conf_params']
        )
        self.parameters['fqdn'] = socket.getfqdn()
        super(ConfigureCollectd, self).run()
