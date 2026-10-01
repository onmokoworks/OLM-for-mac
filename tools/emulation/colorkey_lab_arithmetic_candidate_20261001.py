"""Temporary Lab restoration using the native FLOAT32 comparator operation order."""
from colorkey_lab_mutation_candidate_20261001 import candidate_source as mutation_source

def candidate_source(body):
    body=mutation_source(body)
    old="""float limit = (float)threshold;
	limit += epsilon;
	limit *= 424.4352722167969f;"""
    new="""float limit = (float)threshold * 424.4352722167969f;
	const float epsilon_limit = epsilon * 424.4352722167969f;
	limit = epsilon_limit + limit;"""
    assert body.count(old)==1;body=body.replace(old,new)
    old='if (use_binary_lab76_limits) {'
    assert body.count(old)==1;body=body.replace(old,'if (info.color_space == 3) {')
    old="""hit = std::fabs(cmp[0] - key[0]) <= (key_epsilon + tr) * comp_scale[0]
						    && std::fabs(cmp[1] - key[1]) <= (key_epsilon + tg) * comp_scale[1]
						    && std::fabs(cmp[2] - key[2]) <= (key_epsilon + tb) * comp_scale[2];"""
    new="""float limit_l = key_epsilon + (float)tr;
						float limit_a = key_epsilon + (float)tg;
						float limit_b = key_epsilon + (float)tb;
						limit_l *= comp_scale[0];
						limit_a *= comp_scale[1];
						limit_b *= comp_scale[2];
						hit = std::fabs(cmp[0] - key[0]) <= limit_l
						    && std::fabs(cmp[1] - key[1]) <= limit_a
						    && std::fabs(cmp[2] - key[2]) <= limit_b;"""
    assert body.count(old)==1;return body.replace(old,new)
