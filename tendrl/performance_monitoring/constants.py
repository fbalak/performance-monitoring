CLUSTER_UTILIZATION = "cluster_utilization"
SYSTEM_UTILIZATION = "system_utilization"
USED = "used"
TOTAL = "total"
PERCENT_USED = "percent_used"
STATUS_UP = "up"
STATUS_NOT_MONITORED = "not_monitored"
STATUS_DOWN = "down"
WARNING = "WARNING"
CRITICAL = "CRITICAL"
WARNING_ALERTS = "warning_alerts"
CRITICAL_ALERTS = "critical_alerts"
CLUSTER = 'cluster'
NODE = 'node'
THROUGHPUT = "throughput"
CLUSTER_THROUGHPUT = "cluster_%s" % THROUGHPUT
SYSTEM_THROUGHPUT = "system_%s" % THROUGHPUT
NODE_THROUGHPUT = "node_%s" % THROUGHPUT
LATENCY = "latency"
AVERAGE = "average"
IOPS = 'iops'
SWAP = "swap"
SWAP_TOTAL = "swap_aggregated"
CPU = "cpu"
STORAGE = "storage"
SUPPORTED_ALERT_TYPES = [
    "utilization",
    "status"
]
