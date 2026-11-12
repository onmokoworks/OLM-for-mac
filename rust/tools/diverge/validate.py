"""Real native acceptance suite, using built stage-dump plugins and real originals."""
import argparse
from pathlib import Path
import capture
import minimize
import olm_diverge as d
import stage_maps


def validate(originals, directional, distance, out, historical_case=None, harness=None):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    summary = {'runs': {}, 'sources': {}, 'all_passed': False}
    for name in ('olm_diverge.py', 'stage_maps.py', 'capture.py', 'minimize.py'):
        summary['sources'][name] = d.witness.sha256(d.HERE/name)
    try:
        for plugin, candidate, index, stage in [('directional', directional, 372, 'rotate.forward'),
                                                 ('distance', distance, 0, 'gaussian.row')]:
            for injected in (False, True):
                label = plugin + ('-injected' if injected else '-clean')
                case = stage_maps.build(plugin, originals/stage_maps.PINS[plugin][0], candidate,
                                        inject=index if injected else -1)
                d.write_json(out/(label+'.json'), case)
                r = d.run(case, out/label)
                assert r['classification'] == ('divergent' if injected else 'exact'), r
                if injected:
                    assert r['first_divergent_stage'] == stage
                    assert r['stages'][1]['different_elements'] == 1
                    assert r['stages'][2]['different_elements'] > 0, 'injection did not reach output'
                    first = r['stages'][1]['first_difference']
                    assert int(first['candidate']['bits'],16)-int(first['reference']['bits'],16) == 1
                    assert r['reproducer_verified']
                summary['runs'][label] = {'classification': r['classification'], 'first': r['first_divergent_stage'],
                    'different_elements': [s['different_elements'] for s in r['stages']],
                    'first_difference': r['stages'][1]['first_difference'],
                    'report_sha256': d.witness.sha256(out/label/'report.json')}
                print(label, r['classification'], r['first_divergent_stage'], flush=True)
        case = stage_maps.build('distance', originals/stage_maps.PINS['distance'][0], distance, historical=True)
        r = d.run(case, out/'historical-small')
        assert r['first_divergent_stage'] == 'gaussian.row' and r['reproducer_verified']
        reduced = minimize.minimize(out/'historical-small/reproducer.json', out/'historical-small-minimized')
        assert reduced['one_minimal_under_single_word_zeroing']
        summary['runs']['historical-small'] = {'first': r['first_divergent_stage'], 'reduction': reduced}
        if historical_case:
            for sse in (False, True):
                label = 'historical-case39' + ('-sse' if sse else '-current')
                r = capture.capture(historical_case, distance, out/label, historical=sse, harness=harness)
                if sse:
                    assert r['render']['status'] == 'mismatched'
                    assert r['render']['comparison']['mismatching_samples'] == 1706
                    assert r['first_divergent_mapped_stage']['stage'] == 'gaussian.column'
                else:
                    assert r['classification'] == 'render_and_mapped_stages_exact', r
                assert all(all(c['capture_equals_replay'].values()) for c in r['captures'])
                summary['runs'][label] = {'classification': r['classification'], 'render': r['render']['status'],
                    'first': r['first_divergent_mapped_stage'], 'comparison': r['render'].get('comparison'),
                    'report_sha256': d.witness.sha256(out/label/'capture-report.json')}
                print(label, r['classification'], flush=True)
        summary['all_passed'] = True
        return summary
    finally:
        d.write_json(out/'validation.json', summary)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--originals', type=Path, required=True)
    p.add_argument('--directional', type=Path, required=True)
    p.add_argument('--distance', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--historical-case', type=Path)
    p.add_argument('--harness', type=Path)
    a = p.parse_args()
    validate(a.originals, a.directional, a.distance, a.out, a.historical_case, a.harness)
