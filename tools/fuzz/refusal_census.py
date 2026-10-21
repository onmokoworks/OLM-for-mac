#!/usr/bin/env python3
"""Rank RadialBlur admission guards by the fuzz refusals they cause.

Reads a campaign report produced by run.py (which records refusal_guards when
the candidate binary emits OLM_REFUSAL_TRACE lines) and reports how many legal
cases each named guard rejected per route. Counts are facts from the report;
the intent column is a one-line quote of the guard's source comment when one
exists, otherwise a tag-derived description (marked as such).
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
GUI = '\u2014'


def parse_entry(entry):
    """'Function:tag@line' -> ('Function:tag', line); tolerate the older form."""
    guard, _, line = entry.rpartition('@')
    if not guard:
        return entry, None
    try:
        return guard, int(line)
    except ValueError:
        return entry, None


def defaults(controls):
    def build(w, h):
        result = {}
        for declaration in controls:
            kind = declaration['kind']
            value = declaration['default_value']
            if kind == 'p':
                x, y = declaration['default_components']
                value = [round(x*w/100*65536)/65536, round(y*h/100*65536)/65536]
            elif kind == 'a':
                value = declaration['default_components'][0]
            elif kind in ('i', 'b', 'u'):
                value = int(value)
            result[declaration['slot']] = value
        return result
    return build


def load_controls():
    path = ROOT/'reports/radialblur_public_getters_aligned_20261001.json'
    declarations = json.loads(path.read_text())['native_parameter_declarations']
    kinds = {1: 'i', 3: 'a', 4: 'b', 6: 'p', 7: 'u', 10: 's'}
    return [dict(kind=kinds[p['param_type']], **p) for p in declarations
            if p['param_type'] in kinds]


def source_line(source, function, tag):
    marker = f'OLM_RADIAL_REFUSAL("{tag}")'
    for number, line in enumerate(source.splitlines(), 1):
        if marker in line:
            return number
    marker = f'OLM_RADIAL_ERROR("{tag}"'
    for number, line in enumerate(source.splitlines(), 1):
        if marker in line:
            return number
    return None


def features(case, defaults_for):
    values = {p['slot']: p['value'] for p in case['parameters']}
    base = defaults_for(*case['geometry'])
    slots = Counter({slot: 1 for slot, value in values.items() if value != base[slot]})
    w, h = case['geometry']
    longest = max(w, h)
    geometry = ('1x1' if (w, h) == (1, 1) else 'thin' if min(w, h) == 1
                else 'small' if longest <= 24 else 'mid' if longest <= 64 else 'large')
    return {'slots': slots, 'depth': case['depth'], 'profile': case['profile'],
            'geometry': geometry, 'values': values}


def top_features(cases, defaults_for):
    slots, depths, profiles = Counter(), Counter(), Counter()
    for case in cases:
        feature = features(case, defaults_for)
        slots.update(feature['slots'])
        depths[feature['depth']] += 1
        profiles[feature['profile']] += 1
    slot_text = ', '.join(f'slot {slot} ({count})' for slot, count in slots.most_common(3))
    depth_text = '/'.join(f'{depth} ({count})' for depth, count in depths.most_common(3))
    profile_text = ', '.join(f'{name} ({count})' for name, count in profiles.most_common(3))
    return (f'params {slot_text or "no non-default slot"}; '
            f'depth {depth_text or GUI}; profile {profile_text or GUI}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--markdown', type=Path, help='write the table to this path')
    parser.add_argument('--source', type=Path,
                        default=ROOT/'mac/OLMRadialBlur/OLMRadialBlur.cpp')
    args = parser.parse_args()

    report = json.loads(args.report.read_text())
    source = args.source.read_text()
    controls = load_controls()
    defaults_for = defaults(controls)
    rows = report['cases']
    by_index = {row['index']: row for row in rows}

    counts = Counter()              # (guard, route) -> refusals
    lines = {}
    case_sets = defaultdict(set)    # guard -> case indices
    unattributed = Counter()        # (route, error) -> refusals
    total = Counter()               # route -> refusals
    total_516 = Counter()
    attributed = Counter()
    attributed_516 = Counter()
    for row in rows:
        attribution = row.get('refusal_guards') or {}
        for route, result in row['result']['routes'].items():
            if result['status'] != 'refusal':
                continue
            error = result.get('error')
            total[route] += 1
            if error == 516:
                total_516[route] += 1
            entries = attribution.get(route) or []
            if not entries:
                unattributed[(route, error)] += 1
                continue
            guard, line = parse_entry(entries[0])
            counts[(guard, route)] += 1
            attributed[route] += 1
            if error == 516:
                attributed_516[route] += 1
            case_sets[guard].add(row['index'])
            if line is not None:
                lines[guard] = line

    guards = sorted({guard for guard, _ in counts}, key=lambda g: (-sum(
        counts[(g, route)] for route in ('classic', 'smart')), g))
    header = ('| rank | guard id | file:line | Classic | Smart | top triggers '
              '(non-default params, depth, profile) | intent |')
    divider = '|---:|---|---|---:|---:|---|---|'
    table = [header, divider]
    for rank, guard in enumerate(guards, 1):
        function, _, tag = guard.partition(':')
        line = lines.get(guard) or source_line(source, function, tag)
        cases = [by_index[index] for index in sorted(case_sets[guard])]
        location = f'`mac/OLMRadialBlur/OLMRadialBlur.cpp:{line}`' if line else GUI
        classic = counts[(guard, 'classic')] or GUI
        smart = counts[(guard, 'smart')] or GUI
        table.append(f"| {rank} | `{guard}` | {location} | {classic} | {smart} | "
                     f"{top_features(cases, defaults_for)} | {intent(guard)} |")

    unattributed_total = sum(unattributed.values())
    all_refusals = sum(total.values())
    covered = sum(attributed.values())
    summary = [
        f"total refusals: {all_refusals} ({', '.join(f'{r}={total[r]}' for r in total)})",
        f"attributed to a named guard: {covered}/{all_refusals} "
        f"({100.0*covered/all_refusals:.2f}%)",
        f"ERROR 516 attribution: {sum(attributed_516.values())}/{sum(total_516.values())} "
        f"({100.0*sum(attributed_516.values())/max(1,sum(total_516.values())):.2f}%)",
        f"non-516 attributed: {covered-sum(attributed_516.values())} "
        f"(work-budget/error returns, not admission guards)",
    ]
    for (route, error), count in sorted(unattributed.items()):
        summary.append(f"unattributed {route} error {error}: {count} (not an admission guard return)")

    text = '\n'.join(summary) + '\n\n' + '\n'.join(table) + '\n'
    print(text)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(text)
    return 0


INTENTS = {
    'RenderZoomTyped:unadmitted-zoom-profile':
        'Rejects any Zoom control tuple that misses every exact-fixture predicate.',
    'RenderZoomTyped:unadmitted-zoom-noise-inner-profile':
        '"These branches are not yet backed by an actual-AEX worker/output contract."',
    'RenderZoomTyped:generic-size-variation-topology':
        'Requires a general size-variation source topology for the generic profile.',
    'RenderZoomTyped:generic-size-noise-topology':
        'Requires a general source topology for the generic size+noise profile.',
    'RenderRotationTyped:unadmitted-rotation-profile':
        'Rejects any Rotation control tuple that misses every exact-fixture predicate.',
    'RenderRotationTyped:unadmitted-two-stage-profile':
        'Admits Rotation only through the generic families or a proven exact tuple.',
    'RenderRotationTyped:generic-size-variation-topology':
        'Requires a general size-variation source topology for the generic profile.',
    'RenderRotationTyped:generic-size-noise-topology':
        'Requires a general source topology for the generic size+noise profile.',
    'RenderWorld:type3-zero-noise':
        '"A zero/negative Type-3 amount does not belong to the sole admitted NV25 layer tuple."',
    'RenderWorld:type3-nonzoom':
        '"Only the exact-source 9x7 Zoom/NV25 tuple is admitted below."',
    'RenderWorld:generic-world-not-admitted':
        '"must either pass that family\'s complete world/layout contract or stop here."',
    'ValidateNoiseLayerWorld:noise-world-invalid':
        'Type-3 Noise Layer was requested but the host provided no usable world.',
}


def intent(guard):
    return INTENTS.get(guard, 'tag-derived: ' + guard.split(':', 1)[1].replace('-', ' '))


if __name__ == '__main__':
    sys.exit(main())
