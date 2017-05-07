# This util has been borrowed with minor deviations from calamari
# as in:
# https://github.com/ceph/calamari/blob/master/rest-api/calamari_rest/views/v1.py#L219

from collections import defaultdict

CRIT_STATES = set(
    [
        'stale',
        'down',
        'peering',
        'inconsistent',
        'incomplete',
        'inactive'
    ]
)
WARN_STATES = set(
    [
        'creating',
        'recovery_wait',
        'recovering',
        'replay',
        'splitting',
        'degraded',
        'remapped',
        'scrubbing',
        'repair',
        'wait_backfill',
        'backfilling',
        'backfill_toofull'
    ]
)
OKAY_STATES = set(
    [
        'active',
        'clean'
    ]
)


def _pg_counter_helper(states, classifier, count, stats):
    matched_states = classifier.intersection(states)
    if len(matched_states) > 0:
        stats[0] += count
        for state in matched_states:
            stats[1][state] += count
        return True
    return False


def _calculate_pg_counters(pgs_by_state):
    all_states = CRIT_STATES | WARN_STATES | OKAY_STATES
    ok, warn, crit = [[0, defaultdict(int)] for _ in range(3)]
    for state_name, count in pgs_by_state.iteritems():
        states = map(lambda s: s.lower(), state_name.split("+"))  # noqa
        if _pg_counter_helper(states, CRIT_STATES, count, crit):
            pass
        elif _pg_counter_helper(states, WARN_STATES, count, warn):
            pass
        elif _pg_counter_helper(states, OKAY_STATES, count, ok):
            pass
        else:
            # Uncategorised state, assume it's critical.This shouldn't usually
            # happen, but want to avoid breaking if ceph adds a state.
            crit[0] += count
            for state in states:
                if state not in all_states or state in CRIT_STATES:
                    crit[1][state] += count
    return {
        'ok': {
            'count': ok[0],
            'states': dict(ok[1]),
        },
        'warn': {
            'count': warn[0],
            'states': dict(warn[1]),
        },
        'critical': {
            'count': crit[0],
            'states': dict(crit[1]),
        },
    }
