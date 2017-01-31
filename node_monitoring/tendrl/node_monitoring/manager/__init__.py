import gevent.event
import gevent.greenlet
import logging
import signal
from tendrl.commons import manager as commons_manager
from tendrl.node_monitoring.central_store \
    import NodeMonitoringEtcdCentralStore


LOG = logging.getLogger(__name__)


class NodeMonitoringManager(commons_manager.Manager):
    def __init__(self):
        super(
            NodeMonitoringManager,
            self
        ).__init__(
            None,
            tendrl_ns.central_store_thread
        )


def main():
    complete = gevent.event.Event()
    tendrl_ns.central_store_thread = NodeMonitoringEtcdCentralStore()

    tendrl_ns.definitions.save()
    tendrl_ns.config.save()
    tendrl_ns.tendrl_context.save()

    manager = NodeMonitoringManager()
    manager.start()

    def shutdown():
        LOG.info("Signal handler: stopping")
        complete.set()

    gevent.signal(signal.SIGTERM, shutdown)
    gevent.signal(signal.SIGINT, shutdown)

    while not complete.is_set():
        complete.wait(timeout=1)


if __name__ == "__main__":
    main()
