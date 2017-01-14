#!/usr/bin/python


import socket
import sys
from subprocess import check_output
import yaml

tendrl_collectd_severity_map = {
    'FAILURE': 'CRITICAL',
    'WARNING': 'WARNING',
    'OK': 'INFO'
}


def get_notification():
    """
        Collectd forks an instance of this plugin per threshold breach detected
        Read collectd detected threshold breach details from standard input of
        current fork.
        Returns:
        The collectd message as a dict
        The summary of collectd message as a string
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
        Function to transform collectd detected threshold breach message dict
        to a tendrl format by
        1. appending additional information like pid, source, etc..
        2. mapping collectd specified severity to tendrl severity levels.
        Returns:
        Tendrl understandable threshold breach alert as a dict
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
        Post threshold breach tendrl understandable alert dict to node-agent
        exposed socket.
    """
    s = socket.socket()
    host = "127.0.0.1"
    port = 12345
    s.connect((host, port))
    collectd_alert, collectd_message = get_notification()
    tendrl_alert = collectd_to_tendrl_alert(collectd_alert, collectd_message)
    s.send(yaml.safe_dump(tendrl_alert))
    s.shutdown(socket.SHUT_RDWR)


if __name__ == '__main__':
    post_notification_to_node_agent_socket()
