#!/usr/bin/env python3
"""Package measured R06 records, including failures, without changing gate inputs."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/R06-release-gate-closure';OUT=ROOT/'orchestra/reports'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    rows=[]
    indices=(152,153,155,156,157,158,159,167,168,169,170,171,172,174,178,179,181)
    for index in indices:
        d=S/str(index);row=json.loads((d/'planes.json').read_text());runs=json.loads((d/'report.json').read_text())
        assert len(runs['runs'])==4
        assert all(r['status']==dict(status='ok',guards_intact=True,session_clean=True) for r in runs['runs'])
        assert len({r['sha256'] for r in runs['runs']})==1
        assert row['padding_exact'] and 'output' in row['planes']
        assert all(v['repeat_identical'] and v['exact'] and v['different_bytes']==0 and v['first_byte'] is None for v in row['planes'].values())
        rows.append(dict(**row,executions=runs))
    capability=json.loads((S/'capability/report.json').read_text())
    result=dict(status='blocked',scope='17 retained first witnesses; full legacy multi-case suites not closed',radial=rows,capability=capability,gate_table=[dict(check='Generic',before='45 PASS / 8 FAIL (R05)',after='not rerun; gate inputs unchanged'),dict(check='Release aggregate',before='invalid (R05)',after='not rerun; gate inputs unchanged'),dict(check='Radial selected intermediate witnesses',before='unresolved (R05)',after='17 first witnesses exact; fixture165/full command coverage unresolved')],remaining=['Group 1: full-size165, remaining cases/planes and negative assertions in historical commands; no pins changed','Group 2: all 13 R03 runtime/contract failures unadjudicated','Group 3: F40 bindings, historical packages, support documentation and performance bindings unadjudicated','Installed identity/host smoke/Kira Windows-owner renewal: requires real AE/Windows'])
    (OUT/'R06-results.json').write_text(json.dumps(result,indent=2)+'\n')
    files=sorted(p for p in S.rglob('*') if p.is_file() and p.name!='package.log')
    # All scratch here is logs, compressed bytes and trace data, with no builds.
    assert not any(p.name in ('probe','probe.cpp') or 'build' in p.relative_to(S).parts for p in files)
    records=[dict(path=str(p.relative_to(S)),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    archive=OUT/'R06-evidence.tar.xz'
    with tarfile.open(archive,'w:xz') as tar:
        for p in files:tar.add(p,arcname=str(p.relative_to(S)),recursive=False)
    manifest=dict(archive=archive.name,sha256=sha(archive),files=records)
    (OUT/'R06-artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(cases=len(rows),sessions=sum(len(r['executions']['runs']) for r in rows),comparisons=sum(len(r['planes']) for r in rows),intermediate_comparisons=sum(len(r['planes'])-1 for r in rows),different_bytes=0,archive_bytes=archive.stat().st_size,archive_sha256=manifest['sha256'],members=len(files))))
if __name__=='__main__':main()
