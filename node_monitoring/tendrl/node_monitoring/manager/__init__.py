import gevent.event
import gevent.greenlet
import logging
import signal
from tendrl.commons import jobs
from tendrl.node_monitoring.central_store \
    import NodeMonitoringEtcdCentralStore


LOG = logging.getLogger(__name__)


class Manager(object):
    def __init__(self):
        self._job_consumer_thread = jobs.JobConsumerThread()

    def stop(self):
        LOG.info("%s stopping" % self.__class__.__name__)
        self.job_consumer_thread.stop()

    def start(self):
        LOG.info("%s starting" % self.__class__.__name__)
        self._job_consumer_thread.start()

    def join(self):
        LOG.info("%s joining" % self.__class__.__name__)
        self._job_consumer_thread.join()


def main():
    complete = gevent.event.Event()
    tendrl_ns.central_store_thread = NodeMonitoringEtcdCentralStore()

    tendrl_ns.definitions.save()
    tendrl_ns.config.save()
    tendrl_ns.tendrl_context.save()

    manager = Manager()
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
