from tendrl.performance_monitoring.time_series_db.manager \
    import TimeSeriesDBPlugin


class InfluxDbPlugin(TimeSeriesDBPlugin):

    def intialize(self):
        pass

    def get_metric_stats(self, entity_name, metric_name):
        raise NotImplementedError()

    def get_metrics(self, entity_name):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()
