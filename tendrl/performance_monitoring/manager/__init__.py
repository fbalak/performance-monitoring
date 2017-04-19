import etcd
from flask import Flask
from flask import request
from flask import Response
import json
import multiprocessing
import os
import signal
from uuid import UUID
from tendrl.commons.config import ConfigNotFound
from tendrl.commons.event import Event
from tendrl.commons.message import ExceptionMessage
from tendrl.commons.message import Message
from tendrl.commons import TendrlNS
from tendrl.performance_monitoring import PerformanceMonitoringNS
from tendrl.performance_monitoring.aggregator.cluster_summary \
    import ClusterSummarise
from tendrl.performance_monitoring.aggregator.node_summary import NodeSummarise
from tendrl.performance_monitoring.central_store \
    import PerformanceMonitoringEtcdCentralStore
from tendrl.performance_monitoring.configure.configure_cluster_monitoring\
    import ConfigureClusterMonitoring
from tendrl.performance_monitoring.configure.configure_node_monitoring \
    import ConfigureNodeMonitoring
from tendrl.performance_monitoring import constants as \
    pm_consts
from tendrl.performance_monitoring.exceptions \
    import TendrlPerformanceMonitoringException
from tendrl.performance_monitoring.sds import SDSMonitoringManager
from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBManager

app = Flask(__name__)


@app.route("/monitoring/nodes/<node_id>/<resource_name>/stats")
def get_nodestats(node_id, resource_name):
    try:
        node_name = NS.central_store_thread.get_node_name_from_id(
            node_id
        )
        return Response(
            NS.time_series_db_manager.\
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


@app.route(
    "/monitoring/clusters/<cluster_id>/utilization/<utiliation_type>/stats"
)
def get_clusterutilization(cluster_id, utiliation_type):
    try:
        entity_name, metric_name = NS.time_series_db_manager.\
            get_timeseriesnamefromresource(
                resource_name=pm_consts.CLUSTER_UTILIZATION,
                utilization_type=utiliation_type,
                cluster_id=cluster_id
        ).split(
            NS.time_series_db_manager.get_plugin().get_delimeter(),
            1
        )
        # Validate cluster_id. Attempt to fetch clusters/cluster_id fails
        # with EtcdKeyNotFound if cluster if is invalid
        NS.etcd_orm.client.read('/clusters/%s' % cluster_id)
        return Response(
            NS.time_series_db_manager.\
            get_plugin().\
            get_metric_stats(entity_name, metric_name),
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


@app.route("/monitoring/system/<sds_type>/utilization/<utiliation_type>/stats")
def get_sdsutilization(sds_type, utiliation_type):
    try:
        # validate sds-type
        if sds_type not in NS.sds_monitoring_manager.supported_sds:
            raise TendrlPerformanceMonitoringException(
                'Unsupported sds %s' % sds_type
            )
        entity_name, metric_name = NS.time_series_db_manager.\
            get_timeseriesnamefromresource(
                resource_name=pm_consts.SYSTEM_UTILIZATION,
                utilization_type=utiliation_type,
                sds_type=sds_type
        ).split(
            NS.time_series_db_manager.get_plugin().get_delimeter(),
            1
        )
        return Response(
            NS.time_series_db_manager.\
            get_plugin().\
            get_metric_stats(entity_name, metric_name),
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


@app.route("/monitoring/clusters/<cluster_id>/summary")
def get_cluster_summary(cluster_id):
    try:
        cluster_summary = NS.central_store_thread.get_cluster_summary(
            cluster_id
        )
        return Response(
            json.dumps(cluster_summary),
            status=200,
            mimetype='application/json'
        )
    except TendrlPerformanceMonitoringException as ex:
        return Response(
            'Failed to fetch cluster summary for cluster %s.Error %s' % (
                cluster_id,
                str(ex)
            ),
            status=500,
            mimetype='application/json'
        )


@app.route("/monitoring/system/<cluster_type>/summary")
def get_system_summary(cluster_type):
    try:
        if cluster_type not in NS.sds_monitoring_manager.supported_sds:
            raise TendrlPerformanceMonitoringException(
                'Unsupported sds %s' % cluster_type
            )
        summary = NS.central_store_thread.get_system_summary(cluster_type)
        return Response(
            json.dumps(summary),
            status=200,
            mimetype='application/json'
        )
    except TendrlPerformanceMonitoringException as ex:
        return Response(
            'Failed to fetch %s system summary.Error %s' % (
                cluster_type,
                str(ex)
            ),
            status=500,
            mimetype='application/json'
        )


@app.route("/monitoring/nodes/<node_id>/monitored_types")
def get_stat_types(node_id):
    try:
        node_name = NS.central_store_thread.get_node_name_from_id(
            node_id
        )
        return Response (
            NS.time_series_db_manager.get_plugin().get_metrics(node_name),
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
                uuid_string = node_list[index].strip()
                if UUID(
                    uuid_string,
                    version=4
                ).hex == uuid_string.replace('-', ''):
                    node_list[index] = node_list[index].strip()
                else:
                    raise TendrlPerformanceMonitoringException(
                        'Node id %s in the parameter is not a valid uuid' % (
                            uuid_string
                        )
                    )
            summary, ret_code, exs = \
                NS.central_store_thread.get_node_summary(node_list)
        else:
            summary, ret_code, exs = \
                NS.central_store_thread.get_node_summary()
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
            self.api_server = NS.performance_monitoring.config.data[
                'api_server_addr'
            ]
            self.api_port = int(
                NS.performance_monitoring.config.data[
                    'api_server_port'
                ]
            )
            NS.configurator_queue = multiprocessing.Queue()
            NS.sds_monitoring_manager = SDSMonitoringManager()
            self.configure_cluster_monitoring = ConfigureClusterMonitoring()
            self.node_summariser = NodeSummarise()
            self.cluster_summariser = ClusterSummarise()
            self.configure_node_monitoring = ConfigureNodeMonitoring()
        except (ConfigNotFound, TendrlPerformanceMonitoringException):
            raise

    def start(self):
        NS.central_store_thread.start()
        self.node_summariser.start()
        self.cluster_summariser.start()
        self.configure_cluster_monitoring.start()
        self.configure_node_monitoring.start()
        try:
            app.run(host=self.api_server, port=self.api_port, threaded=True)
        except (ValueError, TendrlPerformanceMonitoringException) as ex:
            Event(
                ExceptionMessage(
                    priority="error",
                    publisher=NS.publisher_id,
                    payload={"message": 'Failed to start the api server.',
                             "exception": ex
                             }
                )
            )

            self.stop()

    def stop(self):
        NS.central_store_thread.stop()
        self.configure_cluster_monitoring.stop()
        self.configure_node_monitoring.stop()
        NS.configurator_queue.close()
        self.node_summariser.stop()
        os.system("ps -C tendrl-performance-monitoring -o pid=|xargs kill -9")


def main():
    PerformanceMonitoringNS()
    TendrlNS()
    NS.publisher_id = "performance_monitoring"
    NS.central_store_thread = PerformanceMonitoringEtcdCentralStore()
    NS.time_series_db_manager = TimeSeriesDBManager()
    NS.performance_monitoring.definitions.save()
    NS.performance_monitoring.config.save()

    tendrl_perf_manager = TendrlPerformanceManager()

    def terminate(sig, frame):
        Event(
            Message(
                priority="error",
                publisher=NS.publisher_id,
                payload={"message": "Signal handler: stopping"}
            )
        )
        tendrl_perf_manager.stop()

    signal.signal(signal.SIGINT, terminate)
    tendrl_perf_manager.start()


if __name__ == "__main__":
    main()
