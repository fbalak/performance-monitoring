import ast
import etcd
from flask.ext.api import status
from flask import Flask
from flask import request
import logging
from multiprocessing import Event
from multiprocessing import Process
import urllib2
import yaml


LOG = logging.getLogger(__name__)
persister = None
time_series_db_manager = None
app = Flask(__name__)


@app.route("/monitoring/nodes/<node_id>/<resource_name>/stats")
def get_stats(node_id, resource_name):
    try:
        global persister
        node_name = persister.get_node_name_from_id(
            node_id
        )
        return time_series_db_manager.\
            get_plugin().\
            get_metric_stats(node_name, resource_name)
    except (
        ValueError,
        urllib2.URLError,
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        SyntaxError,
        etcd.EtcdException,
        TypeError
    ) as ex:
        return str(ex), status.HTTP_500_INTERNAL_SERVER_ERROR


@app.route("/monitoring/nodes/<node_id>/monitored_types")
def get_stat_types(node_id):
    try:
        global persister
        node_name = persister.get_node_name_from_id(
            node_id
        )
        return time_series_db_manager.get_plugin().get_metrics(node_name)
    except (
        ValueError,
        urllib2.URLError,
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        SyntaxError,
        etcd.EtcdException,
        TypeError
    ) as ex:
        return str(ex), status.HTTP_500_INTERNAL_SERVER_ERROR


@app.route("/monitoring/nodes/summary")
def get_node_summary():
    try:
        global persister
        # Only 1 filter that is the node list is the only supported filter
        # anything else is simply ignored.
        is_filter = (
            len(request.args) == 1 and
            request.args.items()[0][0] == 'node_id'
        )
        if is_filter:
            node_list = ast.literal_eval(request.args.items()[0][1])
            ret_val = persister.get_node_summary(node_list)
        else:
            ret_val = persister.get_node_summary()
        return yaml.safe_dump(ret_val)
    except (
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        ValueError,
        SyntaxError,
        etcd.EtcdException,
        TypeError
    ) as ex:
        return str(ex), status.HTTP_500_INTERNAL_SERVER_ERROR


class APIManager(Process):

    def __init__(
        self,
        api_host,
        api_port,
        persister_instance,
        timeSeriesDbManager
    ):
        super(APIManager, self).__init__()
        self._complete = Event()
        self.host = api_host
        self.port = api_port
        global persister
        persister = persister_instance
        global time_series_db_manager
        time_series_db_manager = timeSeriesDbManager

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
            time_series_db_manager.stop()
        except Exception as e:
            LOG.error(
                'Exception %s caught while interrupting api server' % str(e),
                exc_info=True
            )
