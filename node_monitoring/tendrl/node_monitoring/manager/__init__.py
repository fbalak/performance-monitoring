import gevent.event
import gevent.greenlet
import signal
from tendrl.commons import manager as commons_manager
from tendrl.commons import TendrlNS
from tendrl.node_monitoring.central_store \
    import NodeMonitoringEtcdCentralStore
from tendrl.node_monitoring import NodeMonitoringNS


class NodeMonitoringManager(commons_manager.Manager):
    def __init__(self):
        super(
            NodeMonitoringManager,
            self
        ).__init__(
            None,
            NS.central_store_thread
        )


def main():
    NodeMonitoringNS()
    TendrlNS()
    NS.type = "monitoring"

    complete = gevent.event.Event()
    NS.central_store_thread = NodeMonitoringEtcdCentralStore()

    NS.node_monitoring.definitions.save()
    NS.node_monitoring.config.save()
    NS.publisher_id = "node_monitoring"

    manager = NodeMonitoringManager()
    manager.start()

    def shutdown():
        Event(
            Message(
                priority="info",
                publisher=NS.publisher_id,
                payload={"message": "Signal handler: stopping"}
            )
        )
        complete.set()

    gevent.signal(signal.SIGTERM, shutdown)
    gevent.signal(signal.SIGINT, shutdown)

    while not complete.is_set():
        complete.wait(timeout=1)


if __name__ == "__main__":
    main()
