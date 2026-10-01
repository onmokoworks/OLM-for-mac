"""Temporary generalization of native in-place Lab comparison state."""
def candidate_source(body):
    old='if (bounded_native_lab76) {\n\t\t\t\t\tLab76ComparatorMutate(key);'
    new='if (info.color_space == 3 || (info.color_space == 4 && info.per_component)) {\n\t\t\t\t\tLab76ComparatorMutate(key);'
    assert body.count(old)==1
    body=body.replace(old,new)
    old='} else if (bounded_native_lab76) {\n\t\t\t\t\tPF_FpLong threshold'
    new='} else if (info.color_space == 3 && !info.per_component) {\n\t\t\t\t\tPF_FpLong threshold'
    assert body.count(old)==1
    return body.replace(old,new)
