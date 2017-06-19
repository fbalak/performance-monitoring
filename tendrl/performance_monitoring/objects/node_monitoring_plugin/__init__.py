from tendrl.commons import objects
from tendrl.commons.utils.time_utils import now


class NodeMonitoringPlugin(objects.BaseObject):
    def __init__(
        self,
        plugin_name=None,
        node_id=None,
        job_id='',
        time_stamp=str(now()),
        *args,
        **kwargs
    ):
        # TODO(anmol_b): Add status to track configuration status and retrial
        # count if auto-retrials are required. node-monitoring which is the
        # consumer of these monitoring configuration jobs, will update success
        # or failure in configuration when the job is picked by it. And retrial
        # counter would be incremented from the only supposed way to load
        # monitoring utils#util#initiate_config_generation jobs to /queue.
        # There unpicked timed-out jobs can then be updated from configuration
        # threads - configure_node_monitoiring and configure_cluster_monitoring
        # before deciding to attempt/re-attempt config generation by looking at
        # job's' status using the job_id here..
        super(NodeMonitoringPlugin, self).__init__(*args, **kwargs)
        self.node_id = node_id
        self.plugin_name = plugin_name
        self.job_id = job_id
        self.time_stamp = time_stamp
        self.value = 'monitoring/plugin_configurations/nodes/{0}/{1}'

    def render(self):
        self.value = self.value.format(self.node_id, self.plugin_name)
        return super(NodeMonitoringPlugin, self).render()
