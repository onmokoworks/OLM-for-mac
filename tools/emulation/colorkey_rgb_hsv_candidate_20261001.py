"""Temporary RGB Euclidean/HSV FLOAT32 comparator and conversion restoration."""
def candidate_source(body):
    pairs=[
        ('else if (mx == g) h = (b - r) * 60.0f / delta + 120.0f;', 'else if (mx == g) h = (b - r) * 60.0f * (1.0f / delta) + 120.0f;'),
        ('else h = (r - g) * 60.0f / delta + 240.0f;', 'else h = (r - g) * 60.0f * (1.0f / delta) + 240.0f;'),
        ('out[0] = h / 360.0f;', 'out[0] = h * 0.0027777778450399637f;'),
        ('hit = (sh - key[0]) <= key_epsilon + tr\n\t\t\t\t\t\t    && std::fabs(cmp[1] - key[1]) <= key_epsilon + tg\n\t\t\t\t\t\t    && std::fabs(cmp[2] - key[2]) <= key_epsilon + tb;', 'hit = (sh - key[0]) <= (float)(key_epsilon + (float)tr)\n\t\t\t\t\t\t    && std::fabs(cmp[1] - key[1]) <= (float)(key_epsilon + (float)tg)\n\t\t\t\t\t\t    && std::fabs(cmp[2] - key[2]) <= (float)(key_epsilon + (float)tb);'),
        ('hit = dist <= std::sqrt(3.0f) * (key_epsilon + threshold);', 'const float limit = std::sqrt(3.0f) * (key_epsilon + (float)threshold);\n\t\t\t\t\t\thit = dist <= limit;'),
        ('hit = std::fabs(cmp[0] - key[0]) <= key_epsilon + tr * comp_scale[0]\n\t\t\t\t\t\t    && std::fabs(cmp[1] - key[1]) <= key_epsilon + tg * comp_scale[1]\n\t\t\t\t\t\t    && std::fabs(cmp[2] - key[2]) <= key_epsilon + tb * comp_scale[2];', 'hit = std::fabs(cmp[0] - key[0]) <= (float)(key_epsilon + (float)tr * comp_scale[0])\n\t\t\t\t\t\t    && std::fabs(cmp[1] - key[1]) <= (float)(key_epsilon + (float)tg * comp_scale[1])\n\t\t\t\t\t\t    && std::fabs(cmp[2] - key[2]) <= (float)(key_epsilon + (float)tb * comp_scale[2]);'),
        ('float mean = (std::fabs(cmp[0] - key[0]) +\n\t\t\t\t\t              std::fabs(cmp[1] - key[1]) +\n\t\t\t\t\t              std::fabs(cmp[2] - key[2])) / 3.0f;\n\t\t\t\t\thit = mean <= threshold;', 'const float d0 = key[0] - cmp[0];\n\t\t\t\t\tconst float d1 = key[1] - cmp[1];\n\t\t\t\t\tconst float d2 = key[2] - cmp[2];\n\t\t\t\t\tfloat squared = d0 * d0;\n\t\t\t\t\tsquared += d1 * d1;\n\t\t\t\t\tsquared += d2 * d2;\n\t\t\t\t\tconst float limit = std::sqrt(3.0f) * (key_epsilon + (float)threshold);\n\t\t\t\t\thit = std::sqrt(squared) <= limit;')]
    for old,new in pairs:
        assert body.count(old)==1,old
        body=body.replace(old,new)
    return body
