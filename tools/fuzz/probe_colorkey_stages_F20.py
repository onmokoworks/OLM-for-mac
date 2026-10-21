#!/usr/bin/env python3
"""Compare retained PF32 matte and final stages using a live AEX-built record.

The public trace uses PNG only to materialize parameters. Native pixel leaves
then consume the exact raw corpus words, never the PNG-converted pixels.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/emulation'))
from aex_loader import AexLoader
from aex_witness import leaf_check
from PIL import Image
from adapters.olmcolorkey import Adapter
from core import load_corpus, raw_diff, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scratch', type=Path, required=True)
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--require-exact', action='store_true')
    args = ap.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT / 'orchestra/state/F20-colorkey-zero-color-and-byte-safe')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    adapter = Adapter(SimpleNamespace(max_size=256, case_timeout=30,
        main=ROOT.parent.parent, worker=args.worker))
    deadline = time.monotonic()+600
    provenance = adapter.prepare(scratch, deadline)
    rows = []
    cases = [(p.stem, load_corpus(p, adapter)[0])
             for p in sorted((ROOT / 'tests/fuzz_corpus/olmcolorkey').glob('*.json'))]
    cases.append(('seed1_case116', adapter.generate(1, 116)))
    for name, case in cases:
        directory = scratch / name
        directory.mkdir(exist_ok=True)
        Image.new('RGBA', (1, 1), (0, 0, 0, 255)).save(directory/'params.png')
        assignments = [f"param_{p['slot']}@{p['slot']}="+
            (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
            for p in case['parameters']]
        process = subprocess.run([str(args.worker), 'render-trace-png', str(adapter.aex),
            str(directory/'params.png'), str(directory/'unused.png'), '--pixel-format', 'argb32f',
            '--watch', 'function=0x9960,arg=stack5,size=1432,occurrence=1', *assignments],
            capture_output=True, check=True, timeout=60, env=adapter.env)
        (directory/'builder-trace.json').write_bytes(process.stdout)
        trace = json.loads(process.stdout)
        assert not trace['render_error'] and trace['guards_intact']
        smart = next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER')
        assert not smart['trace_configuration']['unhookable_watches']
        assert not smart['dropped_memory_witnesses']
        record = bytes.fromhex(smart['memory_witnesses'][0]['before']['hex'])
        assert len(record)==0x598
        (directory/'parameter-record.bin').write_bytes(record)
        loader = AexLoader(str(adapter.aex), verbose=False)
        context, src, dst = loader.host_alloc(len(record)), loader.host_alloc(16), loader.host_alloc(16)
        loader.write_bytes(context, record)
        matte, final = bytearray(), bytearray()
        for offset in range(0, len(case['pixels']), 16):
            loader.write_bytes(src, case['pixels'][offset:offset+16])
            loader.write_bytes(dst, bytes(16))
            leaf_check(loader, 0x1800035d0, [context, 0, 0, src, dst], expected_ret=0)
            matte.extend(loader.read_bytes(dst, 16))
            leaf_check(loader, 0x180004170, [context, 0, 0, src, dst], expected_ret=0)
            final.extend(loader.read_bytes(dst, 16))
        oracle, raw = adapter.oracle(case, directory, deadline, 'smart')
        assert oracle['status']=='ok' and raw == final, name
        matte_case = copy.deepcopy(case)
        for p in matte_case['parameters']:
            if p['slot'] in (1, 23):
                p['value'] = int(p['slot']==1)
        port_matte, port_matte_raw, _ = adapter.candidate(matte_case, directory, 'smart', deadline)
        port_final, port_final_raw, _ = adapter.candidate(case, directory, 'smart', deadline)
        row = dict(name=name, input_sha256=sha(case['pixels']), record_sha256=sha(record),
            public_equals_leaf=True, native_matte_sha256=sha(matte), native_final_sha256=sha(final),
            port_matte=port_matte, port_final=port_final)
        if port_matte['status']=='ok':
            row['matte_diff'] = raw_diff(matte, port_matte_raw, 32)
            row['final_diff'] = raw_diff(final, port_final_raw, 32)
            row['boundary_words'] = [dict(pixel=i//16, source=case['pixels'][i:i+16].hex(),
                native_matte=matte[i:i+16].hex(), port_matte=port_matte_raw[i:i+16].hex(),
                native_final=final[i:i+16].hex(), port_final=port_final_raw[i:i+16].hex())
                for i in range(0,len(final),16)
                if matte[i:i+16]!=port_matte_raw[i:i+16] or final[i:i+16]!=port_final_raw[i:i+16]]
        rows.append(row)
    args.output.write_text(json.dumps(dict(provenance=provenance, cases=rows), indent=2)+'\n')
    print([(r['name'], r.get('matte_diff',{}).get('different_words'),
            r.get('final_diff',{}).get('different_words')) for r in rows])
    if args.require_exact:
        assert all(r['port_matte']['status']=='ok' and r['port_final']['status']=='ok'
                   and r['matte_diff']['different_words']==r['final_diff']['different_words']==0 for r in rows)


if __name__ == '__main__':
    main()
