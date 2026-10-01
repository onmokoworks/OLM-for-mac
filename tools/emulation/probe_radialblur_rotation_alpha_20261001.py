#!/usr/bin/env python3
"""Restore native nonzero-alpha normalization after natural tiny-alpha evidence."""
import json
from pathlib import Path
import sys

import probe_radialblur_rotation_neutral_20261001 as neutral
public = neutral.public
neutral_candidate = neutral.candidate_source


def candidate_source(source):
    source = neutral_candidate(source)
    start = source.index('\t\t\t\t((use_aex_typed_rotation_size_variation_32x18',
                         source.index('const bool use_generic_two_stage'))
    end = source.index('\n\t\t\t\t(use_aex_exact || use_generic_two_stage));', start)
    assert source[start:end].endswith('&& source_components_1_4_9,')
    return source[:start]+'\t\t\t\tuse_aex_two_stage,'+source[end:]


def main():
    # Reuse the exact natural public plane/matrix protocol with a bounded candidate.
    neutral.candidate_source = candidate_source
    neutral.main()
    name = sys.argv[sys.argv.index('--report')+1]
    path = Path(name); report = json.loads(path.read_text())
    report['schema'] = 'radialblur.rotation-neutral-nonzero-alpha-public/1'
    report['dependencies_sha256'][str(Path(__file__).relative_to(public.ROOT))] = public.sha(Path(__file__).read_bytes())
    report['native_sampler_zero_compare_rva'] = '0x121a'
    report['native_sampler_zero_compare_code_sha256'] = public.sha(__import__('pefile').PE(str(public.initial.AEX)).get_data(0x1214, 0x2e))
    report['normalization_condition'] = 'AEX two-stage sampler normalizes every finite nonzero alpha, including alpha below 1e-8.'
    report['claims_not_made'].append('NaN/unordered sampler semantics and arbitrary float input remain separate unverified boundaries.')
    path.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    main()
