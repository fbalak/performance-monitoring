# flake8: noqa
data = """---
namespace.tendrl.performance_monitoring:
  objects:
    Config:
      value: '/_tendrl/config/performance_monitoring'
      data:
        help: "The configurations path"
        type: json
      enabled: true
namespace.tendrl.node_monitoring:
  objects:
    Node:
      atoms:
        cmd:
          enabled: true
          inputs:
            mandatory:
              - Node.cmd_str
          name: "Execute CMD on Node"
          help: "Execute CMD on Node"
          run: tendrl.node_monitoring.atoms.node.cmd.Cmd
          type: Create
          uuid: dc8fff3a-34d9-4786-9282-55eff6abb6c3
        check_node_up:
          enabled: true
          inputs:
            mandatory:
              - Node.fqdn
          outputs:
            - Node.status
          name: "check whether the node is up"
          help: "Checks if a node is up"
          run: tendrl.node_monitoring.atoms.node.check_node_up
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
      value: nodes/$Node_context.node_id/Node
    Service:
      atoms:
       check_service_status:
          enabled: true
          inputs:
            mandatory:
              - Node.fqdn
              - Service.name
          name: "check whether the service is running"
          help: "check whether the service is running"
          run: tendrl.node_monitoring.objects.service.atoms.check_service_status.CheckServiceStatus
          type: Create
          uuid: eda0b13a-7362-48d5-b5ca-4b6d6533a5ab
      attrs:
        name:
          help: "Name of the service"
          type: String
      enabled: true
  flows:
    ConfigureCollectd:
      atoms:
        - tendrl.node_monitoring.objects.Node.atoms.cmd
      help: "Execute given command on given node"
      enabled: true
      inputs:
        mandatory:
          - Node.fqdn
          - plugin_name
          - plugin_conf_params
          - Service.name
      post_run:
        - tendrl.node_monitoring.objects.Service.atoms.check_service_status
      pre_run:
        - tendrl.node_monitoring.objects.Node.atoms.check_node_up
      run: tendrl.node_monitoring.flows.configure_collectd.ConfigureCollectd
      type: Create
      uuid: dc8fff3a-34d9-4786-9282-55eff6abb6c4
      version: 1
tendrl_schema_version: 0.3
"""
