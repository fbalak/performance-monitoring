#!/usr/bin/python


import json
import sys
is_collectd_imported = False
if '/usr/lib64/collectd' in sys.path:
    is_collectd_imported = True
    sys.path.remove('/usr/lib64/collectd')
from etcd import Client as etcd_client
from subprocess import check_output
from tendrl.commons.config import load_config
from tendrl.commons.event import Event
from tendrl.commons.message import Message

tendrl_collectd_severity_map = {
    'FAILURE': 'CRITICAL',
    'WARNING': 'WARNING',
    'OK': 'INFO'
}


config = load_config(
    'node-monitoring',
    '/etc/tendrl/node-monitoring/node-monitoring.conf.yaml'
)

central_store = etcd_client(
    host=config['etcd_connection'],
    port=config['etcd_port']
)

if is_collectd_imported:
    sys.path.append('/usr/lib64/collectd')


'''Collectd forks an instance of this plugin per threshold breach detected
Read collectd detected threshold breach details from standard input of
current fork.'''


def get_notification():
    collectd_alert = {}
    is_end_of_dictionary = False
    for line in sys.stdin:
        if not line.strip():
            is_end_of_dictionary = True
            continue
        if is_end_of_dictionary:
            break
        key, value = line.split(':')
        collectd_alert[key] = value.lstrip()[:-1]
    return collectd_alert, line


'''Function to transform collectd detected threshold breach message dict
to tendrl format by
1. appending additional information like pid, source, etc..
2. mapping collectd specified severity to tendrl severity levels.'''


def collectd_to_tendrl_alert(collectd_alert, collectd_message):
    tendrl_alert = {}
    tendrl_alert['source'] = "collectd"
    tendrl_alert['pid'] = check_output(["pidof", "collectd"]).strip()
    tendrl_alert['time_stamp'] = collectd_alert['Time']
    tendrl_alert['alert_type'] = collectd_alert['Type']
    tendrl_alert['severity'] = tendrl_collectd_severity_map[
        collectd_alert['Severity']
    ]
    tendrl_alert['resource'] = collectd_alert['Plugin']
    tendrl_alert['current_value'] = collectd_alert['CurrentValue']
    tags = {
        'warning_max': collectd_alert['WarningMax'],
        'failure_max': collectd_alert['FailureMax'],
        'message': collectd_message,
    }
    if (
        'Host' in collectd_alert and
        'cluster' in collectd_alert.get('Host')
    ):
        tags['cluster_id'] = collectd_alert.get('Host').split('_')[1]
    if 'PluginInstance' in collectd_alert:
        tags['plugin_instance'] = collectd_alert['PluginInstance']
    tendrl_alert['tags'] = tags
    return tendrl_alert


'''Post threshold breach tendrl understandable alert dict to node-agent
exposed socket.'''


def post_notification_to_node_agent_socket():
    collectd_alert, collectd_message = get_notification()
    tendrl_alert = collectd_to_tendrl_alert(collectd_alert, collectd_message)
    node_context_id = ""
    machine_id = ""
    with open('/etc/machine-id') as f:
        machine_id = f.read().strip('\n')
    node_context_id = central_store.read(
        '/indexes/machine_id/%s' % machine_id
    ).value
    tendrl_alert['node_id'] = node_context_id
    if not node_context_id:
        return
    Event(
        Message(
            "notice",
            "alerting",
            {
                'message': json.dumps(tendrl_alert)
            },
            node_id=node_context_id
        ),
        socket_path=config['logging_socket_path']
    )


if __name__ == '__main__':
    post_notification_to_node_agent_socket()
