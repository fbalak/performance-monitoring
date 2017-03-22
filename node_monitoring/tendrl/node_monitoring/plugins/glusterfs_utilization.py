#!/usr/bin/python

import collectd
import json
import os
import subprocess

PLUGIN_NAME = 'cluster_utilization'
CONFIG = None


def configure_callback(configobj):
    global CONFIG
    CONFIG = {
        c.key: c.values[0] for c in configobj.children
    }


def fetch_utilization():
    args = ["gstatus", "-o", "json"]
    try:
        p = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=open(os.devnull, "r"),
            close_fds=True
        )
        stdout, stderr = p.communicate()
        if stderr == "" and p.returncode == 0:
            result = json.loads(stdout[stdout.index('{'): -1])
        return result
    except Exception as e:
        collectd.info(
            "Failed to fetch cluster and volume utilizations."
            " The error is %s" % (
                str(e)
            )
        )
        return None


def send_metric(
    plugin_name,
    metric_type,
    instance_name,
    value,
    plugin_instance=None
):
    global CONFIG
    metric = collectd.Values()
    metric.plugin = plugin_name
    metric.host = "cluster_%s" % CONFIG['cluster_id']
    metric.type = metric_type
    metric.values = [value]
    metric.type_instance = instance_name
    if plugin_instance:
        metric.plugin_instance = plugin_instance
    metric.dispatch()


def read_callback(data=None):
    global CONFIG
    stats = fetch_utilization()
    if not stats:
        return
    if (
        stats.get('raw_capacity') and
        stats.get('usable_capacity') and
        stats.get('used_capacity') and
        stats.get('raw_capacity') != 0
    ):
        send_metric(
            'cluster_utilization',
            'gauge',
            'total',
            stats.get('raw_capacity')
        )
        send_metric(
            'cluster_utilization',
            'gauge',
            'used',
            stats.get('used_capacity')
        )
        send_metric(
            'cluster_utilization',
            'percent',
            'percent_bytes',
            (
                stats.get('used_capacity') * 100
            ) / (
                stats.get('raw_capacity') * 1.0
            )
        )
    if stats.get('volume_summary'):
        volumes_summary = stats.get('volume_summary')
        for volume_summary in volumes_summary:
            if (
                volume_summary.get('usable_capacity') and
                volume_summary.get('used_capacity')
            ):
                send_metric(
                    'volume_utilization',
                    'gauge',
                    'total',
                    volume_summary.get('usable_capacity'),
                    plugin_instance=volume_summary.get('volume_name')
                )
                send_metric(
                    'volume_utilization',
                    'gauge',
                    'used',
                    volume_summary.get('used_capacity'),
                    plugin_instance=volume_summary.get('volume_name')
                )
                if 'usable_capacity' > 0:
                    send_metric(
                        'volume_utilization',
                        'percent',
                        'percent_bytes',
                        (
                            (
                                volume_summary.get('used_capacity') * 100
                            ) / (
                                volume_summary.get('usable_capacity') * 1.0
                            )
                        ),
                        plugin_instance=volume_summary.get('volume_name')
                    )


collectd.register_config(configure_callback)
collectd.register_read(read_callback, 60)
