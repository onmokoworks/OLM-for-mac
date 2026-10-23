#!/usr/bin/env python3
"""Regenerate the F35 public Smart fixtures using F34's original-AEX audit."""
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('f34', ROOT / 'orchestra/reports/F34-compare-fixtures.py')
f34 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(f34)
f34.S = ROOT / 'orchestra/state/F35-dg-fixture-rebind'


def main():
    try:
        f34.main()
    finally:
        shutil.rmtree(f34.S / "build", ignore_errors=True)
    evidence = json.loads((f34.S / 'comparison.json').read_text())
    for row, name in zip(evidence['rows'], ('zero', 'controlled')):
        old = ROOT / row['fixture']
        target = ROOT / ('refs/fixtures/olmdistancegradation_pf32_owner_17x11'
                         + ('_controlled_source' if name == 'controlled' else '')
                         + '_public_smart_20261023')
        raw = (f34.S / name / 'default-smart.raw').read_bytes()
        assert raw == (f34.S / name / 'F30-smart.raw').read_bytes()
        target.mkdir(exist_ok=True)
        # Expected bytes come only from the original AEX, never the Mac candidate.
        (target / 'source_argb_f32.bin').write_bytes((old / 'source_argb_f32.bin').read_bytes())
        (target / 'output_argb_f32.bin').write_bytes(raw)
        provenance = dict(
            schema='olm.dg.public-smart-fixture/1',
            command='PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/F35-generate-fixtures.py',
            route='public EffectMain Smart PreRender + Smart Render',
            geometry=[17, 11], depth=32, format='little-endian ARGB FLOAT32',
            rowbytes=272, origin=[0, 0], downsample=[1, 1],
            controls=row['parameters'], source_sha256=row['source_sha256'],
            output_sha256=f34.sha(raw), output_bytes=len(raw),
            aex_path=evidence['provenance']['aex_path'],
            aex_sha256=evidence['provenance']['aex_sha256'],
            workers={n: row['aex'][n + '-smart'] for n in ('default', 'F30')},
            supersedes=row['fixture'],
            harness='orchestra/reports/F34-compare-fixtures.py',
            harness_sha256=f34.sha((ROOT / 'orchestra/reports/F34-compare-fixtures.py').read_bytes()),
            scope='Original AEX under Unicorn with host callbacks; not native AE execution')
        (target / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
        print(f'{target.name}: {len(raw)} bytes sha256={f34.sha(raw)} workers identical')


if __name__ == '__main__':
    main()
