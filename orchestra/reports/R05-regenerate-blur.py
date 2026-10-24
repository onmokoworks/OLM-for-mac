#!/usr/bin/env python3
"""Regenerate eligible Blur metadata only after two identical AEX replays."""
import argparse, hashlib, importlib, json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R05-regenerate-stale-bindings/blur'
S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='2',PYTHONDONTWRITEBYTECODE='1')
tempfile.tempdir=str(S)
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation')]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    evidence=[];candidates={}
    matrix_path=ROOT/'refs/conformance/olmblur_pf32_formal_worker_matrix_20260805.json'
    matrix_text=matrix_path.read_text()
    matrix=json.loads(matrix_text)
    for lane,bind in matrix['lanes'].items():
        mod=importlib.import_module('test_olmblur_worker32_'+lane)
        manifest=json.loads((ROOT/bind['manifest']).read_text())
        assert sha(mod.AEX.read_bytes())==matrix['oracle_binary_sha256']
        for spec in mod.CASES:
            old=next(r for r in manifest['cases'] if r['id']==spec['id'])
            assert all(old[k]==v for k,v in spec.items()),('parameter drift',lane,spec['id'])
            source = mod.source_bytes(spec['width'],spec['height'],spec.get('mixed_alpha',False),spec.get('pattern','')) if lane=='legacy' else mod.source_bytes(spec['width'],spec['height'])
            assert sha(source)==old['source_sha256'],('source drift',lane,spec['id'])
            a,am=mod.run_case(spec);b,bm=mod.run_case(spec)
            assert a==b and am==bm,('nondeterministic',lane,spec['id'])
            assert sha(a)==old['expected_sha256'],('oracle drift',lane,spec['id'])
            evidence.append(dict(lane=lane,id=spec['id'],runs=2,identical=True,source_sha256=sha(source),sha256=sha(a),metadata=am,generator_sha256=sha(Path(mod.__file__).read_bytes())))
        subprocess.run([sys.executable,str(ROOT/bind['smoke'])],cwd=ROOT,check=True)
        for key in ('production_source','replay'):
            current=sha((ROOT/bind[key]).read_bytes())
            matrix_text=matrix_text.replace(bind[key+'_sha256'],current)
            bind[key+'_sha256']=current
    assert json.loads(matrix_text)==matrix
    candidates[matrix_path]=matrix_text
    owner=importlib.import_module('test_olmblur_pf16_worker_sources_exported_public_owner_20260813')
    old=json.loads(owner.REPORT.read_text());a=owner.live();b=owner.live()
    assert a==b,'owner nondeterministic'
    for key in old:
        if key!='identities':assert a[key]==old[key],('owner nonidentity change',key)
    candidates[owner.REPORT]=json.dumps(a,indent=2,sort_keys=True)+'\n'
    evidence.append(dict(owner_rows=len(a['rows']),runs=2,identical=True,non_identity_fields_unchanged=True))
    for path,payload in candidates.items():
        target=S/path.name;target.write_text(payload)
        if args.apply:path.write_text(payload)
    (S/'verification.json').write_text(json.dumps(dict(applied=args.apply,rows=evidence,candidates={str(p.relative_to(ROOT)):sha(v.encode()) for p,v in candidates.items()},aex_sha256=matrix['oracle_binary_sha256']),indent=2)+'\n')
    print('verified',len(evidence)-1,'PF32 cases and',len(a['rows']),'PF16 owner cases; applied',args.apply,flush=True)
if __name__=='__main__':main()
