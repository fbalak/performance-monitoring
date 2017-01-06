import ast
import etcd
from flask import Flask
from flask import request
import logging
from multiprocessing import Event
from multiprocessing import Process
from tendrl.common.config import ConfigNotFound
from tendrl.common.config import TendrlConfig
from tendrl.common.etcdobj.etcdobj import Server as etcd_server
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBManager
import urllib2

config = TendrlConfig()

LOG = logging.getLogger(__name__)


app = Flask(__name__)


def get_node_name_from_id(node_id):
    try:
        etcd_kwargs = {
            'port': int(config.get("common", "etcd_port")),
            'host': config.get("common", "etcd_connection")
        }
        etcd_client = etcd_server(etcd_kwargs=etcd_kwargs).client
        node_name_path = '/nodes/%s/Node_context/fqdn' % node_id
        return etcd_client.read(node_name_path).value
    except (
        ConfigNotFound,
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        ValueError,
        SyntaxError,
        etcd.EtcdException,
        TypeError
    ) as ex:
        raise ex


@app.route("/monitoring/nodes/<node_id>/<resource_name>/stats")
def get_stats(node_id, resource_name):
    try:
        node_name = get_node_name_from_id(node_id)
        return TimeSeriesDBManager().\
            get_plugin().\
            get_metric_stats(node_name, resource_name)
    except (
        ConfigNotFound,
        ValueError,
        urllib2.URLError,
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        SyntaxError,
        etcd.EtcdException,
        TypeError
    ) as ex:
        raise ex


@app.route("/monitoring/nodes/<node_id>/monitored_types")
def get_stat_types(node_id):
    try:
        node_name = get_node_name_from_id(node_id)
        return TimeSeriesDBManager().get_plugin().get_metrics(node_name)
    except (
        ConfigNotFound,
        ValueError,
        urllib2.URLError,
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        SyntaxError,
        etcd.EtcdException,
        TypeError
    ) as ex:
        raise ex


@app.route("/monitoring/nodes/summary")
def get_node_summary():
    try:
        etcd_kwargs = {
            'port': int(config.get("common", "etcd_port")),
            'host': config.get("common", "etcd_connection")
        }
        etcd_client = etcd_server(etcd_kwargs=etcd_kwargs).client
        monitoring_node_det = etcd_client.read(
            '/monitoring/summary/',
            recursive=True
        )
        ret_val = []
        # Only 1 filter that is the node list is the only supported filter
        # anything else is simply ignored.
        is_filter = (
            len(request.args) == 1 and
            request.args.items()[0][0] == 'node_id'
        )
        if is_filter:
            node_list = ast.literal_eval(request.args.items()[0][1])
        for child in monitoring_node_det._children:
            if 'summary' in child['key']:
                node_summary = {
                    'node_id': child['key'][len('/monitoring/summary/'):],
                    'summary': child['value']
                }
                if is_filter:
                    if node_summary['node_id'] in node_list:
                        ret_val.append(node_summary)
                else:
                    ret_val.append(node_summary)
        return str(ret_val)
    except (
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        ValueError,
        SyntaxError,
        etcd.EtcdException,
        TypeError
    ) as ex:
        raise ex


class APIManager(Process):

    def __init__(self):
        super(APIManager, self).__init__()
        self._complete = Event()
        try:
            self.host = config.get(
                "tendrl_performance",
                "api_server_addr"
            )
            self.port = config.get(
                "tendrl_performance",
                "api_server_port"
            )
        except ConfigNotFound as ex:
            LOG.error(
                'Failed to start api manager. Error %s' % str(ex),
                exc_info=True
            )
            raise ex

    def run(self):
        try:
            app.run(host=self.host, port=self.port)
            while not self._complete.is_set():
                self._complete.wait(timeout=1)
        except (ValueError, urllib2.URLError) as ex:
            LOG.error('Failed to start the api server. Error %s' %
                      ex, exc_info=True)
            self.stop()

    def stop(self):
        try:
            TimeSeriesDBManager().stop()
        except Exception as e:
            LOG.error(
                'Exception %s caught while interrupting api server' % str(e),
                exc_info=True
            )
