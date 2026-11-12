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

from PIL import Image

HERE = Path(__file__).resolve().parent
RUST = HERE.parents[1]
PLUGINS = {
    'color-keep': 'ColorKeep', 'olm-blur': 'OLMBlur', 'olm-color-key': 'OLMColorKey',
    'olm-directional-blur': 'OLMDirectionalBlur', 'olm-distance-gradation': 'DistanceGradation',
    'olm-kirakira': 'OLMKiraKira', 'olm-radial-blur': 'OLMRadialBlur',
    'olm-smoother': 'OLMSmoother', 'olm-smoother2': 'OLMSmoother2',
    'olm-toon-dilate': 'OLMToonDilate',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--originals', required=True, type=Path)
    p.add_argument('--harness', required=True, type=Path)
    p.add_argument('--kira-harness', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path, help='fresh local evidence directory')
    p.add_argument('--jobs', type=int, choices=range(1, 5), default=2)
    p.add_argument('--only', choices=PLUGINS, help='diagnostic subset; NEVER publishes golden.json')
    p.add_argument('--limit', type=int, help='diagnostic first N cases; NEVER publishes golden.json')
    p.add_argument('--bin-dir', type=Path, help='already-built release binaries; default builds workspace package')
    a = p.parse_args()
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
    hashes, evidence = {}, {'schema': 1, 'platform': platform.platform(), 'plugins': {}}
    failures = []
    for crate, name in PLUGINS.items():
        if a.only and a.only != crate:
            continue
        harness = a.kira_harness if name == 'OLMKiraKira' else a.harness
        original = a.originals/f'{name}.aex'
        directory = a.out/name
        exe = a.bin_dir/f'golden-{crate}.exe'
        subprocess.run([str(exe), '--export', str(directory)], check=True)
        cases = json.loads((directory/'cases.json').read_text())
        if a.limit is not None:
            cases = cases[:a.limit]

        def verify(case):
            ident = case['id']
            work = directory/ident
            work.mkdir()
            image = work/'input.png'
            Image.frombytes('RGBA', (case['width'], case['height']),
                            (directory/f'{ident}.rgba').read_bytes()).save(image)
            ratio = {'numerator': 1, 'denominator': case['denominator']}
            request = {'schema_version': 1, 'assignments': case['assignments'],
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
            output = work/'original.png'
            result = oracle.run_process([harness, '--headless', oracle.ROUTES[route][1],
                original, image, output, request_path], timeout,
                env_overrides=oracle.frame_deadline_environment(timeout))
            (work/'process.json').write_text(json.dumps(result, indent=2)+'\n')
            row = {'id': ident, 'route': route, 'rust_sha256': case['sha256'],
                   'request_sha256': sha(request_path), 'input_sha256': sha(image),
                   'returncode': result['returncode'], 'timeout': result['timeout']}
            if result['timeout'] or result['returncode'] != 0:
                row['status'] = 'original_error'
                return row
            reference = oracle.load_output(output, case['depth']).tobytes()
            pure = (directory/f'{ident}.raw').read_bytes()
            assert hashlib.sha256(pure).hexdigest() == case['sha256']
            row['original_sha256'] = hashlib.sha256(reference).hexdigest()
            row['status'] = 'exact' if reference == pure else 'mismatch'
            if reference != pure:
                row['different_bytes'] = sum(x != y for x, y in zip(reference, pure))
                row['lengths'] = [len(reference), len(pure)]
            return row

        with ThreadPoolExecutor(max_workers=a.jobs) as pool:
            rows = list(pool.map(verify, cases))
        evidence['plugins'][name] = {'original_sha256': sha(original),
            'harness_sha256': sha(harness), 'runner_sha256': sha(exe),
            'cases': rows, 'exact': sum(r['status'] == 'exact' for r in rows)}
        failures.extend(r for r in rows if r['status'] != 'exact')
        hashes.update((r['id'], r['rust_sha256']) for r in rows if r['status'] == 'exact')
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
    assert len(hashes) == 522 and len(evidence['plugins']) == 10
    temporary = HERE/'golden.json.tmp'
    temporary.write_text(json.dumps(hashes, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    temporary.replace(HERE/'golden.json')
    # Keep compact identities/counts; full requests/process logs remain local.
    summary = {name: {k:v for k,v in item.items() if k!='cases'} for name,item in evidence['plugins'].items()}
    (HERE/'verification.json').write_text(json.dumps({'schema':1,'platform':evidence['platform'],
        'golden_sha256':sha(HERE/'golden.json'),'plugins':summary}, indent=2)+'\n')
    print('Published 522 golden hashes: every raw output byte equals its original AEX')


if __name__ == '__main__':
    main()
