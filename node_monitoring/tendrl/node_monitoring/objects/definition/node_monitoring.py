# flake8: noqa
data = """---
namespace.tendrl.node_monitoring:
  objects:
    Config:
      attrs:
        data:
          help: Configuration data of node_monitoring for this Tendrl deployment
          type: str
        etcd_connection:
          help: Host/IP of the etcd central store for this Tendrl deployment
          type: str
        etcd_port:
          help: Port of the etcd central store for this Tendrl deployment
          type: str
        file_path:
          default: /etc/tendrl/node-monitoring/node-monitoring.conf.yaml
          help: Path to the performance_monitoring tendrl configuration
          type: str
        log_cfg_path:
          default: /etc/tendrl/node-monitoring/node-monitoring_logging.yaml
          help: The logging configuration file path
          type: str
        tendrl_ansible_exec_file:
          default: $HOME/.tendrl/node-monitoring/ansible_exec
          help: The ansible exe path prefix
          type: str
      enabled: true
      value: _tendrl/config/node_monitoring
      list: _tendrl/config/node_monitoring
      help: node monitoring integration component configuration
    NodeContext:
      attrs:
        machine_id:
          help: "Unique /etc/machine-id"
          type: str
        fqdn:
          help: "FQDN of the Tendrl managed node"
          type: str
        node_id:
          help: "Tendrl ID for the managed node"
          type: str
        tags:
          help: "The tags associated with this node"
          type: str
        status:
          help: "Node status"
          type: str
      enabled: true
      list: nodes/$NodeContext.node_id/NodeContext
      value: nodes/$NodeContext.node_id/NodeContext
      help: Node Context
    Node:
      atoms:
        Cmd:
          enabled: true
          inputs:
            mandatory:
              - Node.cmd_str
          outputs:
            - Node.status
          name: "Execute CMD on Node"
          help: "Execute CMD on Node"
          run: tendrl.node_monitoring.objects.Node.atoms.cmd.Cmd
          type: Create
          uuid: dc8fff3a-34d9-4786-9282-55eff6abb6c3
        CheckNodeUp:
          enabled: true
          inputs:
            mandatory:
              - Node.fqdn
          outputs:
            - Node.status
          name: "check whether the node is up"
          help: "Checks if a node is up"
          run: tendrl.node_monitoring.objects.Node.atoms.check_node_up.CheckNodeUp
          type: Create
          uuid: eda0b13a-7362-48d5-b5ca-4b6d6533a5ab
      attrs:
        cmd_str:
          type: String
        fqdn:
          type: String
        status:
          type: Boolean
      enabled: true
      value: nodes/$NodeContext.node_id/Node
      list: nodes/
      help: 'Node'
    Service:
      atoms:
       CheckServiceStatus:
          enabled: true
          inputs:
            mandatory:
              - Node.fqdn
              - Service.name
          outputs:
            - status
          name: "check whether the service is running"
          help: "check whether the service is running"
          run: tendrl.node_monitoring.objects.Service.atoms.check_service_status.CheckServiceStatus
          type: Create
          uuid: eda0b13a-7362-48d5-b5ca-4b6d6533a5ab
      attrs:
        name:
          help: "Name of the service"
          type: String
      enabled: true
      value: nodes/$NodeContext.node_id/Services
      list: nodes/$NodeContext.node_id/Services
      help: "Service"
    TendrlContext:
      enabled: True
      attrs:
        integration_id:
          help: "Tendrl managed/generated cluster id for the sds being managed by Tendrl"
          type: String
        sds_name:
          help: "Name of the Tendrl managed sds, eg: 'gluster'"
          type: String
        sds_version:
          help: "Version of the Tendrl managed sds, eg: '3.2.1'"
          type: String
        node_id:
          help: "Tendrl ID for the managed node"
          type: String
      value: nodes/$Node_context.node_id/TendrlContext
      list: nodes/$Node_context.node_id/TendrlContext
      help: "Tendrl context"
  flows:
    ConfigureCollectd:
      atoms:
        - tendrl.node_monitoring.objects.Node.atoms.cmd.Cmd
      help: "Execute given command on given node"
      enabled: true
      inputs:
        mandatory:
          - Node.fqdn
          - plugin_name
          - plugin_conf_params
          - Service.name
      post_run:
        - tendrl.node_monitoring.objects.Service.atoms.check_service_status.CheckServiceStatus
      pre_run:
        - tendrl.node_monitoring.objects.Node.atoms.check_node_up.CheckNodeUp
      run: tendrl.node_monitoring.flows.configure_collectd.ConfigureCollectd
      type: Create
      uuid: dc8fff3a-34d9-4786-9282-55eff6abb6c4
      version: 1
tendrl_schema_version: 0.3
"""
