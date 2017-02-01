import etcd
from flask import Flask
from flask import request
from flask import Response
import json
import logging
from multiprocessing import Event
from multiprocessing import Process
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
import urllib2


LOG = logging.getLogger(__name__)
time_series_db_manager = None
app = Flask(__name__)


@app.route("/monitoring/nodes/<node_id>/<resource_name>/stats")
def get_stats(node_id, resource_name):
    try:
        node_name = tendrl_ns.central_store_thread.get_node_name_from_id(
            node_id
        )
        return Response(
            time_series_db_manager.\
            get_plugin().\
            get_metric_stats(node_name, resource_name),
            status=200,
            mimetype='application/json'
        )
    except (
        ValueError,
        urllib2.URLError,
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        SyntaxError,
        etcd.EtcdException,
        TypeError
    ) as ex:
        return Response(str(ex), status=500, mimetype='application/json')


@app.route("/monitoring/nodes/<node_id>/monitored_types")
def get_stat_types(node_id):
    try:
        node_name = tendrl_ns.central_store_thread.get_node_name_from_id(
            node_id
        )
        return Response (
            time_series_db_manager.get_plugin().get_metrics(node_name),
            status=200,
            mimetype='application/json'
        )
    except (
        ValueError,
        urllib2.URLError,
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        SyntaxError,
        etcd.EtcdException,
        TypeError
    ) as ex:
        return Response(
            str(ex),
            status=500,
            mimetype='application/json'
        )


@app.route("/monitoring/nodes/summary")
def get_node_summary():
    try:
        # Only 1 filter that is the node list is the only supported filter
        # anything else is simply ignored.
        is_filter = (
            len(request.args) == 1 and
            request.args.items()[0][0] == 'node_ids'
        )
        if is_filter:
            node_list = (request.args.items()[0][1]).split(",")
            for index, node in enumerate(node_list):
                node_list[index] = node_list[index].strip()
            ret_val = tendrl_ns.central_store_thread.get_node_summary(node_list)
        else:
            ret_val = tendrl_ns.central_store_thread.get_node_summary()
        return Response(
            json.dumps(ret_val),
            status=200,
            mimetype='application/json'
        )
    except (
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        ValueError,
        SyntaxError,
        etcd.EtcdException,
        TendrlPerformanceMonitoringException,
        TypeError
    ) as ex:
        return Response(
            str(ex),
            status=500,
            mimetype='application/json'
        )


class APIManager(Process):

    def __init__(
        self,
        api_host,
        api_port,
        timeSeriesDbManager
    ):
        super(APIManager, self).__init__()
        self._complete = Event()
        self.host = api_host
        self.port = api_port
        global time_series_db_manager
        time_series_db_manager = timeSeriesDbManager

    def run(self):
        try:
            app.run(host=self.host, port=self.port, threaded=True)
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
