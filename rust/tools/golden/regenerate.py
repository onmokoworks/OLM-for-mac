"""Windows-only: export pure renders, compare every byte with original AEX, then publish hashes.

No original is copied. An error/mismatch prevents golden.json replacement.
The shared oracle owns and reaps each harness process tree in a Windows Job.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


HERE = Path(__file__).resolve().parent
RUST = HERE.parents[1]
PLUGINS = {
    'color-keep': 'ColorKeep', 'olm-blur': 'OLMBlur', 'olm-color-key': 'OLMColorKey',
    'olm-directional-blur': 'OLMDirectionalBlur', 'olm-distance-gradation': 'DistanceGradation',
    'olm-kirakira': 'OLMKiraKira', 'olm-radial-blur': 'OLMRadialBlur',
    'olm-smoother': 'OLMSmoother', 'olm-smoother2': 'OLMSmoother2',
    'olm-toon-dilate': 'OLMToonDilate',
    'olm-uv-map': 'OLMUVMap', 'olm-anti-anti-alias': 'OLMAntiAntiAlias',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def merge_subset(old_hashes, old_exclusions, hashes, exclusions, names):
    expected = {f'{name}-{index:02}-{depth}' for name in names
                for index in range(18) for depth in ((8,16) if name=='OLMSmoother' else (8,16,32))}
    if set(hashes) & set(exclusions) or set(hashes) | set(exclusions) != expected:
        raise ValueError('subset must contain every planned case exactly once')
    keep = lambda values: {k:v for k,v in values.items() if k.split('-')[0] not in names}
    return {**keep(old_hashes), **hashes}, {**keep(old_exclusions), **exclusions}


def main():
    from PIL import Image
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--originals', required=True, type=Path)
    p.add_argument('--harness', required=True, type=Path)
    p.add_argument('--kira-harness', type=Path, help='defaults to ordinary shared harness')
    p.add_argument('--out', required=True, type=Path, help='fresh local evidence directory')
    p.add_argument('--jobs', type=int, choices=range(1, 4), default=2)
    p.add_argument('--only', choices=PLUGINS, help='diagnostic subset; NEVER publishes golden.json')
    p.add_argument('--limit', type=int, help='diagnostic first N cases; NEVER publishes golden.json')
    p.add_argument('--bin-dir', type=Path, help='already-built release binaries; default builds workspace package')
    p.add_argument('--plugins', nargs='+', choices=PLUGINS, help='publish complete verified replacements for these plug-ins; preserve others')
    a = p.parse_args()
    a.kira_harness = a.kira_harness or a.harness
    if a.plugins and (a.only or a.limit is not None):
        p.error('--plugins cannot be combined with diagnostic --only/--limit')
    selected = set(a.plugins or ([a.only] if a.only else PLUGINS))
    if platform.system() != 'Windows':
        p.error('golden regeneration requires native Windows original AEX execution')
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=False)
    for path in (a.originals, a.harness, a.kira_harness):
        if not path.is_absolute() or not path.exists():
            p.error(f'absolute existing path required: {path}')
    spec = importlib.util.spec_from_file_location('golden_oracle', RUST/'tools/oracle/olm_oracle.py')
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    if a.bin_dir is None:
        subprocess.run(['cargo', 'build', '--release', '-p', 'olm-golden', '--bins'], cwd=RUST, check=True)
        a.bin_dir = Path(os.environ.get('CARGO_TARGET_DIR', RUST/'target'))/'release'
    a.bin_dir = a.bin_dir.resolve()
    hashes, exclusions = {}, {}
    evidence = {'schema': 1, 'platform': platform.platform(), 'plugins': {}}
    failures = []
    for crate, name in PLUGINS.items():
        if crate not in selected:
            continue
        harness = a.kira_harness if name == 'OLMKiraKira' else a.harness
        original = a.originals/f'{name}.aex'
        if not original.exists():
            matches = list(a.originals.glob(f'*/*/Plugins/64/2025/{name}.aex'))
            if len(matches) != 1:
                raise ValueError(f'expected exactly one 2025 original for {name}: {matches}')
            original = matches[0]
        directory = a.out/name
        exe = a.bin_dir/f'golden-{crate}.exe'
        subprocess.run([str(exe), '--export', str(directory)], check=True)
        cases = json.loads((directory/'cases.json').read_text())
        if a.limit is not None:
            cases = cases[:a.limit]
        # Predeclared count, applied to EVERY Radial case, never retry-until-pass.
        repeats = 4 if name == 'OLMRadialBlur' else 1
        for repeat in range(1, repeats):
            replay = a.out/f'{name}-pure-{repeat}'
            subprocess.run([str(exe), '--export', str(replay)], check=True)
            assert (replay/'cases.json').read_bytes() == (directory/'cases.json').read_bytes()
            for case in cases:
                assert (replay/f"{case['id']}.raw").read_bytes() == (directory/f"{case['id']}.raw").read_bytes(), 'pure output is unstable'

        def verify(case):
            ident = case['id']
            work = directory/ident
            work.mkdir()
            image = work/'input.png'
            Image.frombytes('RGBA', (case['width'], case['height']),
                            (directory/f'{ident}.rgba').read_bytes()).save(image)
            for layer in case.get('layers', []):
                Image.frombytes('RGBA', (layer['width'], layer['height']),
                    (directory/layer['file']).read_bytes()).save(work/f"layer-{layer['slot']}.png")
            ratio = {'numerator': 1, 'denominator': case['denominator']}
            assignments = [dict(x) for x in case['assignments']]
            for item in assignments:
                if 'layer' in item:
                    item['layer'] = str(work/item['layer'])
            request = {'schema_version': 1, 'assignments': assignments,
                'host_context': {'mask_scene': {'masks': []}, 'spatial': {
                    'downsample_x': ratio, 'downsample_y': ratio,
                    'pixel_aspect_ratio': {'numerator': 1, 'denominator': 1},
                    'full_resolution_width': case['width']*case['denominator'],
                    'full_resolution_height': case['height']*case['denominator']}},
                'render_settings': {'premultiplication': 'straight',
                    'color_management': {'enabled': False, 'working_space': None},
                    'linear_light': False, 'renderer': 'software'}}
            request_path = work/'request.json'
            request_path.write_text(json.dumps(request, indent=2)+'\n')
            route = ('classic' if name == 'OLMSmoother' else 'smart') + str(case['depth'])
            timeout = 300 if name in ('OLMRadialBlur', 'DistanceGradation') else 120
            row = {'id': ident, 'route': route, 'rust_sha256': case['sha256'],
                   'fingerprint': case['fingerprint'], 'pure_repeats': repeats,
                   'request_sha256': sha(request_path), 'input_sha256': sha(image),
                   'layers': [{**layer, 'sha256': sha(work/f"layer-{layer['slot']}.png")} for layer in case.get('layers', [])]}
            pure = (directory/f'{ident}.raw').read_bytes()
            assert hashlib.sha256(pure).hexdigest() == case['sha256']
            originals, exact, errors = [], [], []
            for repeat in range(repeats):
                output = work/f'original-{repeat}.png'
                result = oracle.run_process([harness, '--headless', oracle.ROUTES[route][1],
                    original, image, output, request_path], timeout,
                    env_overrides=oracle.frame_deadline_environment(timeout))
                (work/f'process-{repeat}.json').write_text(json.dumps(result, indent=2)+'\n')
                if result['timeout'] or result['returncode'] != 0:
                    errors.append({'repeat':repeat,'timeout':result['timeout'],'returncode':result['returncode']})
                    continue
                reference = oracle.load_output(output, case['depth']).tobytes()
                originals.append(hashlib.sha256(reference).hexdigest())
                exact.append(reference == pure)
            row['original_sha256'] = originals
            row['exact_repeats'] = exact
            if errors:
                row.update(status='original_error', errors=errors)
            elif all(exact):
                row['status'] = 'exact'
            elif len(set(originals)) > 1 and any(exact) and repeats == 4:
                row['status'] = 'excluded_original_nondeterminism'
            else:
                row['status'] = 'mismatch'
            return row

        with ThreadPoolExecutor(max_workers=a.jobs) as pool:
            rows = list(pool.map(verify, cases))
        evidence['plugins'][name] = {'original_sha256': sha(original),
            'harness_sha256': sha(harness), 'runner_sha256': sha(exe),
            'cases': rows, 'exact': sum(r['status'] == 'exact' for r in rows),
            'excluded': sum(r['status'] == 'excluded_original_nondeterminism' for r in rows)}
        failures.extend(r for r in rows if r['status'] not in ('exact','excluded_original_nondeterminism'))
        hashes.update((r['id'], r['rust_sha256']) for r in rows if r['status'] == 'exact')
        exclusions.update((r['id'],r['fingerprint']) for r in rows if r['status']=='excluded_original_nondeterminism')
        (a.out/'verification.json').write_text(json.dumps(evidence, indent=2)+'\n')
        print(f"{name}: {sum(r['status']=='exact' for r in rows)}/{len(rows)} original-exact", flush=True)
        for row in rows:
            if row['status'] != 'exact':
                print(json.dumps(row), flush=True)
    if failures:
        raise SystemExit(f'{len(failures)} failures: golden.json NOT changed; inspect {a.out}')
    if a.only or a.limit is not None:
        print('Diagnostic subset only: golden.json NOT changed')
        return
    expected_count = sum(36 if PLUGINS[c] == 'OLMSmoother' else 54 for c in selected)
    assert len(hashes) + len(exclusions) == expected_count
    assert len(evidence['plugins']) == len(selected)
    radial = evidence['plugins'].get('OLMRadialBlur', {}).get('cases', [])
    if radial:
        admitted = [r for r in radial if r['status']=='exact']
        assert len(admitted) >= 30, 'too few deterministic Radial cases'
        assert len({r['id'].split('-')[1] for r in admitted}) == 18
        assert all(sum(r['route']==f'smart{depth}' for r in admitted) >= 10 for depth in (8,16,32))
    previous = json.loads((HERE/'verification.json').read_text())
    if a.plugins:
        hashes, exclusions = merge_subset(
            json.loads((HERE/'golden.json').read_text()),
            json.loads((HERE/'exclusions.json').read_text()), hashes, exclusions,
            {PLUGINS[c] for c in selected})
    temporary = HERE/'golden.json.tmp'
    temporary.write_text(json.dumps(hashes, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    temporary.replace(HERE/'golden.json')
    (HERE/'exclusions.json').write_text(json.dumps(exclusions, indent=2, sort_keys=True)+'\n')
    # Keep compact identities/counts; full requests/process logs remain local.
    summary = {name: {k:v for k,v in item.items() if k!='cases'} for name,item in evidence['plugins'].items()}
    if a.plugins:
        summary = {**previous['plugins'], **summary}
    excluded_cases = [r for r in previous.get('excluded_cases', [])
                      if r['id'].split('-')[0] not in {PLUGINS[c] for c in selected}]
    excluded_cases += [r for r in radial if r['status']=='excluded_original_nondeterminism']
    (HERE/'verification.json').write_text(json.dumps({'schema':1,'platform':evidence['platform'],
        'golden_sha256':sha(HERE/'golden.json'),'plugins':summary,
        'excluded_cases':excluded_cases}, indent=2)+'\n')
    print(f'Published {len(hashes)} golden hashes: every raw output byte equals its original AEX; {len(exclusions)} evidenced nondeterministic exclusions')


if __name__ == '__main__':
    main()
