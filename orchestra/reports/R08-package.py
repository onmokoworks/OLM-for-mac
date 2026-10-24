#!/usr/bin/env python3
"""Package R08 evidence and verify every committed archive member."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/R08-radial-fullsize-trace';OUT=ROOT/'orchestra/reports'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 report=json.loads((S/'165/report.json').read_text());assert len(report['runs'])==4
 assert len({r['sha256'] for r in report['runs']})==1
 assert all(v['repeat_identical'] and v['different_bytes']==0 for v in report['planes'].values())
 legacy=json.loads((S/'legacy/results.json').read_text());assert len(legacy)==18
 build=Path.home()/'.cache/olm-emu/worker-R08-trace/build.json';(S/'worker-build.json').write_bytes(build.read_bytes())
 files=[p for p in S.rglob('*') if p.is_file() and p.suffix in ('.json','.zlib','.log','.txt','.bin') and 'fixture' not in str(p.relative_to(S))]
 files=sorted(files);archive=OUT/'R08-evidence.tar.xz'
 with tarfile.open(archive,'w:xz',preset=3) as t:
  for p in files:t.add(p,arcname=str(p.relative_to(S)),recursive=False)
 manifest=dict(archive=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,files=[dict(path=str(p.relative_to(S)),bytes=p.stat().st_size,sha256=sha(p)) for p in files])
 with tarfile.open(archive) as t:
  for row in manifest['files']:
   with t.extractfile(row['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
 (OUT/'R08-artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 results=dict(status='blocked',scope='full-size165 captured and refreshed; complete 18-command closure remains unresolved',fullsize=report,fullsize_command_status=json.loads((S/'refreshed165.json').read_text())['status'],legacy=legacy,production_source_sha256=sha(ROOT/'mac/OLMRadialBlur/OLMRadialBlur.cpp'),worker_build=json.loads(build.read_text()))
 results['worker_build'].pop('source_manifest',None)
 results['checkpoint_capability']=json.loads((S/'extra-plane-capability/report.json').read_text())
 results['legacy_plane_drift']=json.loads((S/'legacy-plane-drift.json').read_text())
 (OUT/'R08-results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(dict(members=len(files),bytes=manifest['bytes'],sha256=manifest['sha256'],legacy_pass=sum(r['returncode']==0 for r in legacy),legacy_fail=sum(r['returncode']!=0 for r in legacy))))
if __name__=='__main__':main()
