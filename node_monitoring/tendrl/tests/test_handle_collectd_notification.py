import io
import subprocess
import sys
from tendrl.node_monitoring.plugins.handle_collectd_notification \
    import collectd_to_tendrl_alert
from tendrl.node_monitoring.plugins.handle_collectd_notification \
    import get_notification


class StringIO(io.StringIO):

    def __init__(self, value=''):
        value = value.encode('utf8', 'backslashreplace').decode('utf8')
        io.StringIO.__init__(self, value)

    def write(self, msg):
        io.StringIO.write(self, msg.encode(
            'utf8', 'backslashreplace').decode('utf8'))


class TestHandleCollectdNotification(object):
    def get_sample_valid_notification(self):
        return '''Severity: FAILURE
Time: 1481345075.096
Host: dhcp43-30.lab.eng.blr.redhat.com
Plugin: swap
Type: percent
TypeInstance: used
DataSource: value
CurrentValue: 2.399964e+00
WarningMin: nan
WarningMax: 1.000000e+00
FailureMin: nan
FailureMax: 2.000000e+00

Host dhcp43-30.lab.eng.blr.redhat.com,plugin swap type percent (instance used)\
: Data source "value" is currently 2.399964. That is above failure threshold \
of 2.000000.

'''

    def stub_stdin(self):
        stdin = sys.stdin

        def cleanup():
            sys.stdin = stdin

        sys.stdin = StringIO(self.get_sample_valid_notification())

    def test_collectd_notification_parsing(self, monkeypatch):
        self.stub_stdin()

        def get_pid_of_collectd(proces_params):
            return '21688'

        monkeypatch.setattr(subprocess, 'check_output', get_pid_of_collectd)
        notification_dict, notification_summary = get_notification()
        expected_notification = {
            'CurrentValue': '2.399964e+00',
            'WarningMax': '1.000000e+00',
            'Severity': 'FAILURE',
            'Plugin': 'swap',
            'FailureMin': 'nan',
            'WarningMin': 'nan',
            'TypeInstance': 'used',
            'Host': 'dhcp43-30.lab.eng.blr.redhat.com',
            'DataSource': 'value',
            'FailureMax': '2.000000e+00',
            'Time': '1481345075.096',
            'Type': 'percent'
        }
        assert notification_dict == expected_notification
        tendrl_alert = collectd_to_tendrl_alert(
            notification_dict,
            notification_summary
        )
        expected_tendrl_alert = {
            'resource': u'swap',
            'severity': u'FAILURE',
            'tags': {
                'message': u'Host dhcp43-30.lab.eng.blr.redhat.com,plugin swap \
type percent (instance used): Data source "value" is currently\
 2.399964. That is above failure threshold of 2.000000.\n',
                'warning_max': u'1.000000e+00',
                'failure_max': u'2.000000e+00'
            },
            'pid': '21688',
            'source': 'collectd',
            'host': u'dhcp43-30.lab.eng.blr.redhat.com',
            'current_value': u'2.399964e+00',
            'time_stamp': u'1481345075.096',
            'type': u'percent'
        }
        assert tendrl_alert == expected_tendrl_alert
