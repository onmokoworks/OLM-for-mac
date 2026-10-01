"""Temporary restoration of YUV/YCrCb FLOAT32 limits and COMISS predicates."""


def candidate_source(body):
    old = '''hit = std::fabs(cmp[0] - key[0]) <= t0 + key_epsilon
					    && std::fabs(un(cmp[1]) - un(key[1])) <= t1 + key_epsilon;'''
    new = '''const float limit0 = (float)t0 + key_epsilon;
					const float limit1 = (float)t1 + key_epsilon;
					hit = !(std::fabs(cmp[0] - key[0]) > limit0)
					    && !(std::fabs(un(cmp[1]) - un(key[1])) > limit1);'''
    assert body.count(old) == 1
    body = body.replace(old, new)
    old = '''hit = std::fabs(cmp[0] - key[0]) <= t0 + key_epsilon
					    && std::fabs(cmp[1] - key[1]) <= t1 + key_epsilon;'''
    new = '''const float limit0 = (float)t0 + key_epsilon;
					const float limit1 = (float)t1 + key_epsilon;
					hit = !(std::fabs(cmp[0] - key[0]) > limit0)
					    && !(std::fabs(cmp[1] - key[1]) > limit1);'''
    assert body.count(old) == 1
    return body.replace(old, new)
