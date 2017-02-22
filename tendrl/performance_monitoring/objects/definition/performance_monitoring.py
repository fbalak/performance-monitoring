# flake8: noqa
data = """---
namespace.tendrl.performance_monitoring:
  objects:
    Definition:
      enabled: True
      help: "Definition"
      value: _tendrl/definitions/performance_monitoring
      list: _tendrl/definitions/performance_monitoring
      attrs:
        master:
          help: performance monitoring definitions
          type: String
    PerformanceMonitoringSummary:
      attrs:
        node_id:
          type: str
        cpu_usage:
          type: dict
        memory_usage:
          type: dict
        storage_usage:
          type: dict
        alert_count:
          type: str
      enabled: true
      value: monitoring/summary/nodes/$NodeContext.node_id
      list: monitoring/summary/nodes
      help: "Node Summary"
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
    TendrlContext:
      enabled: True
      attrs:
        integration_id:
          help: "Tendrl managed id for performance-integration"
          type: String
        sds_name:
          help: "Name of the Tendrl managed sds, eg: 'gluster'"
          type: String
        sds_version:
          help: "Version of the Tendrl managed sds, eg: '3.2.1'"
          type: String
        node_id:
          help: "Tendrl ID for the node"
          type: String
      value: nodes/$NodeContext.node_id/TendrlContext
      list: nodes/$NodeContext.node_id/TendrlContext
      help: "Tendrl context"
    Config:
      attrs:
        data:
          help: Configuration data of performance-monitoring for this Tendrl deployment
          type: str
        etcd_connection:
          help: Host/IP of the etcd central store for this Tendrl deployment
          type: str
        etcd_port:
          help: Port of the etcd central store for this Tendrl deployment
          type: str
        file_path:
          default: /etc/tendrl/performance-monitoring/performance-monitoring.conf.yaml
          help: Path to the performance_monitoring tendrl configuration
          type: str
        api_server_addr:
          default: 0.0.0.0
          help: The ip interface on which the api server needs to be deployed
          type: str
        api_server_port:
          default: 5000
          help: The port on which the api server needs to be deployed
          type: str
        log_cfg_path:
          default: /etc/tendrl/performance-monitoring/performance-monitoring_logging.yaml
          help: The logging configuration file path
          type: str
        time_series_db:
          default: graphite
          help: The name of time series db used
          type: str
        time_series_db_server:
          default: 127.0.0.1
          help: The ip/hostname of node on which time series db has been deployed
          type: str
        time_series_db_port:
          default: 80
          help: The port on which time series db can be accessed
          type: str
      enabled: true
      value: _tendrl/config/performance_monitoring
      list: _tendrl/config/performance_monitoring
      help: performance monitoring integration component configuration
tendrl_schema_version: 0.3
"""
