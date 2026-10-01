"""Restore the third threshold sign gate, separate from the ignored color component."""
from colorkey_yuv_threshold_candidate_20261001 import candidate_source as first_two_limits


def candidate_source(body):
    body = first_two_limits(body)
    pairs = [
        ('PF_FpLong t1 = info.per_component ? info.threshold_g : info.threshold;',
         'PF_FpLong t1 = info.per_component ? info.threshold_g : info.threshold;\n'
         '\t\t\t\t\tPF_FpLong t2 = info.per_component ? info.threshold_b : info.threshold;'),
        ('t1 = info.per_component ? info.thresholds_g[i] : info.thresholds[i];',
         't1 = info.per_component ? info.thresholds_g[i] : info.thresholds[i];\n'
         '\t\t\t\t\t\tt2 = info.per_component ? info.thresholds_b[i] : info.thresholds[i];'),
        ('const float limit1 = (float)t1 + key_epsilon;',
         'const float limit1 = (float)t1 + key_epsilon;\n'
         '\t\t\t\t\tconst float limit2 = (float)t2 + key_epsilon;'),
    ]
    for old, new in pairs:
        assert body.count(old) == 2
        body = body.replace(old, new)
    for last in ('std::fabs(un(cmp[1]) - un(key[1]))', 'std::fabs(cmp[1] - key[1])'):
        old = f'&& !({last} > limit1);'
        new = f'&& !({last} > limit1)\n\t\t\t\t\t    && limit2 >= 0.0f;'
        assert body.count(old) == 1
        body = body.replace(old, new)
    return body
