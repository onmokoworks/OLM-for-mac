"""Temporary Lab94 scalar FLOAT32 threshold materialization restoration."""
def candidate_source(body):
    old='hit = Lab94Distance(key, cmp) <= (float)((double)(key_epsilon + threshold) * 352.978);'
    new="""float limit = key_epsilon + (float)threshold;
						limit = (float)((double)limit * 352.978);
						hit = Lab94Distance(key, cmp) <= limit;"""
    assert body.count(old)==1
    return body.replace(old,new)
