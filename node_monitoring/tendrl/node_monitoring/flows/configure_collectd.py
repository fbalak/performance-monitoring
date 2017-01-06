import socket

from tendrl.node_agent.flows.flow import Flow


class ConfigureCollectd(Flow):

    def run(self):
        self.parameters['Node.cmd_str'] = "config_manager %s '%s'" % (
            self.parameters['plugin_name'],
            self.parameters['plugin_conf_params'])
        self.parameters['fqdn'] = socket.getfqdn()
        super(ConfigureCollectd, self).run()
