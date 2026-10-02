#!/usr/bin/env python3
"""Locate first natural Strength differences before final output composition."""
import inspect
import json
from pathlib import Path

import probe_radialblur_strength_20261002 as strength
import probe_radialblur_zoom_fade_20261002 as zoom
import probe_radialblur_rotation_neutral_20261001 as rotation

public = strength.public


def cases():
    zoom_case = next(c for c in strength.independent_cases() if c['family'] == 1 and
        c['depth'] == 32 and c['group'] == 'outer' and
        next(p['value'] for p in c['parameters'] if p['slot'] == 4) == 65)
    params = public.initial.settings(2, 9, 7)
    changes = {4: 2000, 20: 10, 21: 2.25, 22: 37.5, 24: 33.3, 25: 2,
        27: 53, 29: 3.4, 7: 37, 13: 31, 17: 2.5, 18: 17}
    for param in params:
        if param['slot'] in changes: param['value'] = changes[param['slot']]
    rotation_case = dict(family=2, geometry=[9, 7], pattern='diagonal', depth=32,
        state='strength_rotation_cap', parameters=params)
    return [zoom_case, rotation_case]


def probe(worker, parent, directory, source):
    directory.mkdir(parents=True, exist_ok=False)
    before = strength.before_source()
    # Permit the original legal values without correcting any math. This
    # counterfactual isolates the first algorithm difference from admission.
    for side in ['outer', 'inner']:
        before = before.replace(f'info.{side}_strength <= 64 &&', f'info.{side}_strength <= 2000 &&')
    rows = []
    for index, case in enumerate(cases()):
        temp = directory/str(index); temp.mkdir()
        raw, frame, _, close, _ = public.native_render(parent, temp, case)
        assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean']
        case = dict(case, reference_raw_sha256=public.sha(raw))
        if case['family'] == 1:
            body = inspect.getsource(zoom.trace).replace('def trace(', 'def strength_trace(')
            body = body.replace("length=next(p['value'] for p in case['parameters'] if p['slot']==13)",
                                "length=next(p['value'] for p in case['parameters'] if p['slot']==4)")
            body = body.replace('occurrence=4', 'occurrence=1')
            namespace = {}; exec(compile(body, '<original-strength-table-trace>', 'exec'), dict(zoom.__dict__), namespace)
            native, gaussian, trace = namespace['strength_trace'](worker, temp, case)
            harness = zoom.plane_harness(); prepare = zoom.passive_source; env_name = 'ZOOM_PROBE_DIRECTORY'
        else:
            native, trace = rotation.trace(worker, temp, case)
            gaussian = b''; harness = rotation.fields.plane_harness(); prepare = lambda text: text
            env_name = 'ROTATION_PLANES_DIRECTORY'
        hp = temp/'planes.cpp'; hp.write_text(harness)
        previous = public.initial.HARNESS; comparisons = {}; hashes = {}
        try:
            public.initial.HARNESS = hp
            for name, text in [('before', before), ('candidate', source)]:
                binary = public.build(temp/name, prepare(text))
                planes = temp/(name+'_planes'); planes.mkdir()
                error, rendered, _ = public.mac_render(binary, temp, case, 'classic',
                    dict(strength.ENV, **{env_name: str(planes)}))
                assert not error; hashes[name] = public.sha(rendered)
                comparisons[name] = {}
                for key, data in native.items():
                    path = planes/(key+('.u8' if key == 'eligible' else '.f32'))
                    actual = path.read_bytes()[:len(data)]
                    assert len(actual) == len(data)
                    if key == 'eligible':
                        result = dict(byte_count=len(data), different_bytes=sum(a != b for a, b in zip(data, actual)),
                            native_sha256=public.sha(data), mac_sha256=public.sha(actual))
                    else: result = rotation.fields.compare_words(data, actual)
                    comparisons[name][key] = result
        finally: public.initial.HARNESS = previous
        assert hashes['candidate'] == case['reference_raw_sha256']
        assert all(not c.get('different_words', c.get('different_bytes')) for c in comparisons['candidate'].values())
        rows.append(dict(case=case, original_trace=trace, comparisons=comparisons, raw_sha256=hashes,
            counterfactual_source_sha256=public.sha(before.encode()), candidate_source_sha256=public.sha(source.encode()),
            native_gaussian_sha256=public.sha(gaussian) if gaussian else None))
        print('STRENGTH_NATURAL', case['family'], {k: v.get('different_words', v.get('different_bytes')) for k, v in comparisons['before'].items()}, flush=True)
    return rows


if __name__ == '__main__':
    import sys
    result = probe(Path('/tmp/radial_windows_reference_v2_20261001/target/release/aex-guest-worker'),
        Path('/tmp/radial_doublecast_reference_20261001/target/release/aex-guest-worker'),
        Path(sys.argv[1]), strength.candidate_source(strength.before_source()))
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2)+'\n')
