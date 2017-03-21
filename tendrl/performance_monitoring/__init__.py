try:
    from gevent import monkey
except ImportError:
    pass
else:
    monkey.patch_all()

from tendrl.commons import TendrlNS


class PerformanceMonitoringNS(TendrlNS):
    def __init__(
        self,
        ns_name='performance_monitoring',
        ns_src='tendrl.performance_monitoring'
    ):
        super(PerformanceMonitoringNS, self).__init__(ns_name, ns_src)
