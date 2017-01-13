#!/usr/bin/python


import json
import socket
from subprocess import check_output
import sys

tendrl_collectd_severity_map = {
    'FAILURE': 'CRITICAL',
    'WARNING': 'WARNING',
    'OK': 'INFO'
}

# When Collectd's threshold plugin detects breach of configured threshold
# it creates a fork of this plugin which is configured as NotificationExec
# plugin with the details of threshold breach on plugins STDIN


def get_notification():
    """
        Parse the threshold breach details from STDIN into a dict of fields
        and a summary message.
    """
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


def collectd_to_tendrl_alert(collectd_alert, collectd_message):
    """
        Transform the dict into a tendrl understandable structure
    """
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
    if 'PluginInstance' in collectd_alert:
        tags['plugin_instance'] = collectd_alert['PluginInstance']
    tendrl_alert['tags'] = tags
    return tendrl_alert


def post_notification_to_node_agent_socket():
    """
        Post the observed threshold detail to the node-agent exposed socket.
    """
    s = socket.socket()
    host = "127.0.0.1"
    port = 12345
    s.connect((host, port))
    collectd_alert, collectd_message = get_notification()
    tendrl_alert = collectd_to_tendrl_alert(collectd_alert, collectd_message)
    s.send(json.dumps(tendrl_alert))
    s.shutdown(socket.SHUT_RDWR)


if __name__ == '__main__':
    post_notification_to_node_agent_socket()
