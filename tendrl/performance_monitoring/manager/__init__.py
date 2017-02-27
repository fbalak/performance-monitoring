import etcd
from flask import Flask
from flask import request
from flask import Response
import json
import logging
import multiprocessing
import os
import signal
from tendrl.commons.config import ConfigNotFound
from tendrl.performance_monitoring.aggregator.summary import Summarise
from tendrl.performance_monitoring.central_store \
    import PerformanceMonitoringEtcdCentralStore
from tendrl.performance_monitoring.configure.configurator import Configurator
from tendrl.performance_monitoring.configure.configure_monitoring \
    import ConfigureMonitoring
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.objects.config import Config
from tendrl.performance_monitoring.objects.definition import Definition
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBManager
from tendrl.commons.log import setup_logging


app = Flask(__name__)
LOG = logging.getLogger(__name__)


@app.route("/monitoring/nodes/<node_id>/<resource_name>/stats")
def get_stats(node_id, resource_name):
    try:
        node_name = tendrl_ns.central_store_thread.get_node_name_from_id(
            node_id
        )
        return Response(
            tendrl_ns.time_series_db_manager.\
            get_plugin().\
            get_metric_stats(node_name, resource_name),
            status=200,
            mimetype='application/json'
        )
    except (
        ValueError,
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        SyntaxError,
        etcd.EtcdException,
        TypeError,
        TendrlPerformanceMonitoringException
    ) as ex:
        return Response(str(ex), status=500, mimetype='application/json')


@app.route("/monitoring/nodes/<node_id>/monitored_types")
def get_stat_types(node_id):
    try:
        node_name = tendrl_ns.central_store_thread.get_node_name_from_id(
            node_id
        )
        return Response (
            tendrl_ns.time_series_db_manager.get_plugin().get_metrics(node_name),
            status=200,
            mimetype='application/json'
        )
    except (
        ValueError,
        etcd.EtcdKeyNotFound,
        etcd.EtcdConnectionFailed,
        SyntaxError,
        etcd.EtcdException,
        TypeError,
        TendrlPerformanceMonitoringException
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
        summary = []
        ret_code = 200
        exs = ''
        is_filter = (
            len(request.args) == 1 and
            request.args.items()[0][0] == 'node_ids'
        )
        if is_filter:
            node_list = (request.args.items()[0][1]).split(",")
            for index, node in enumerate(node_list):
                node_list[index] = node_list[index].strip()
            summary, ret_code, exs = \
                tendrl_ns.central_store_thread.get_node_summary(node_list)
        else:
            summary, ret_code, exs = \
                tendrl_ns.central_store_thread.get_node_summary()
        return Response(
            json.dumps(summary),
            status=ret_code,
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

class TendrlPerformanceManager(object):

    def __init__(self):
        try:
            self.api_server = tendrl_ns.config.data[
                'api_server_addr'
            ]
            self.api_port = tendrl_ns.config.data[
                'api_server_port'
            ]
            tendrl_ns.configurator_queue = multiprocessing.Queue()
            self.configure_monitoring = ConfigureMonitoring()
            self.configurator = Configurator()
            self.node_summariser = Summarise()
        except (ConfigNotFound, TendrlPerformanceMonitoringException):
            raise

    def start(self):
        self.configure_monitoring.start()
        self.configurator.start()
        self.node_summariser.start()
        try:
            app.run(host=self.api_server, port=self.api_port, threaded=True)
        except (ValueError, TendrlPerformanceMonitoringException) as ex:
            LOG.error(
                'Failed to start the api server. Error %s' % ex,
                exc_info=True
            )
            self.stop()

    def stop(self):
        tendrl_ns.configurator_queue.close()
        self.node_summariser.stop()
        os.system("ps -C tendrl-performance-monitoring -o pid=|xargs kill -9")


def main():
    tendrl_ns.central_store_thread = PerformanceMonitoringEtcdCentralStore()
    tendrl_ns.time_series_db_manager = TimeSeriesDBManager()
    tendrl_ns.monitoring_config_init_nodes = []
    tendrl_ns.definitions.save()
    tendrl_ns.config.save()

    tendrl_perf_manager = TendrlPerformanceManager()

    def terminate(sig, frame):
        LOG.error("Signal handler: stopping", exc_info=True)
        tendrl_perf_manager.stop()

    signal.signal(signal.SIGINT, terminate)
    tendrl_perf_manager.start()


if __name__ == "__main__":
    main()
