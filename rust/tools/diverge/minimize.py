"""Bounded stage-input reducer. Preserve the same divergent stage and binary pins.

Zero equal f32 input elements on both sides; never change geometry, pointers,
parameters, CPU mode, injection settings or expected status. This is a structural
reproducer, not a claim of globally minimal image/parameter search.
"""
import argparse
import copy
from pathlib import Path
import olm_diverge as d


def minimize(case_path, out, buffer='input', budget=64, timeout=30):
    if not 1 <= budget <= 1024:
        raise ValueError('budget must be 1..1024')
    case_path, out = Path(case_path).resolve(), Path(out).resolve()
    case = d.prepare(d.load_json(case_path), case_path.parent)
    if len(case['stages']) != 1 or case['stages'][0]['dtype'] != 'f32':
        raise ValueError('start with a single-stage f32 reproducer')
    raw = []
    for side in ('reference', 'candidate'):
        b = case[side]['witness']['buffers'][buffer]
        if b.get('pointers'):
            raise ValueError('input buffer contains pointers')
        data = Path(b['file']).read_bytes() if 'file' in b else bytes.fromhex(b.get('hex', ''))
        data += bytes([b.get('fill', 0)]) * (b['size'] - len(data))
        raw.append(data)
    if raw[0] != raw[1] or len(raw[0]) % 4:
        raise ValueError('requires identical, whole-f32 input buffer bytes on both sides')
    out.mkdir(parents=True, exist_ok=False)
    current = bytearray(raw[0])
    attempts = []

    def check(data, label):
        proposal = copy.deepcopy(case)
        for side in ('reference', 'candidate'):
            b = proposal[side]['witness']['buffers'][buffer]
            b.pop('file', None)
            b['hex'] = data.hex()
        result = d.run(proposal, out/label, timeout=timeout, reproduce=False)
        if result['classification'] == 'incomplete':
            raise RuntimeError('reducer trial incomplete: '+str(out/label))
        keep = result['first_divergent_stage'] == case['stages'][0]['id']
        attempts.append({'directory': label, 'kept': keep, 'input_sha256': d.digest(data)})
        return keep, proposal

    ok, best = check(current, 'baseline')
    if not ok:
        raise ValueError('input case does not reproduce a difference')
    active = [i for i in range(len(current)//4) if current[i*4:i*4+4] != bytes(4)]
    granularity = 2
    exhausted = False
    while active:
        chunk_size = max(1, (len(active)+granularity-1)//granularity)
        changed = False
        for start in range(0, len(active), chunk_size):
            if len(attempts)-1 >= budget:
                exhausted = True
                break
            trial = bytearray(current)
            removed = active[start:start+chunk_size]
            for i in removed:
                trial[i*4:i*4+4] = bytes(4)
            kept, proposal = check(trial, f'trial-{len(attempts):04}')
            if kept:
                current, best = trial, proposal
                active = [i for i in active if i not in set(removed)]
                granularity = max(2, granularity-1)
                changed = True
                break
        if exhausted:
            break
        if not changed:
            if chunk_size == 1:
                break
            granularity = min(len(active), granularity*2)
    d.write_json(out/'reduced.json', best)
    # Fresh independent replay after the entire reduction.
    final = d.run(best, out/'verified', timeout=timeout, reproduce=False)
    if final['first_divergent_stage'] != case['stages'][0]['id']:
        raise RuntimeError('reduced input did not reproduce on final independent replay')
    summary = {'buffer': buffer, 'initial_nonzero_words': sum(raw[0][i:i+4] != bytes(4) for i in range(0,len(raw[0]),4)),
               'remaining_nonzero_words': len(active), 'remaining_indices': active,
               'budget': budget, 'budget_exhausted': exhausted, 'one_minimal_under_single_word_zeroing': not exhausted,
               'scope': 'fixed geometry/parameters; no global/pixel-crop minimality claim',
               'first_divergent_stage': final['first_divergent_stage'], 'attempts': attempts,
               'final_report': 'verified/report.json', 'reproducer': 'reduced.json'}
    d.write_json(out/'reduction.json', summary)
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('case', type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--buffer', default='input')
    p.add_argument('--budget', type=int, default=64)
    p.add_argument('--timeout', type=float, default=30)
    a = p.parse_args()
    print(minimize(a.case, a.out, a.buffer, a.budget, a.timeout))
