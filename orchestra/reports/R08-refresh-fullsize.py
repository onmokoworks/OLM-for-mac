#!/usr/bin/env python3
"""Refresh only full-size planes proven twice-original-identical and Mac-equal."""
import hashlib,json,shutil,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/R08-radial-fullsize-trace/165'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 r=json.loads((S/'report.json').read_text());assert len(r['runs'])==4 and len({v['sha256'] for v in r['runs']})==1
 assert all(v['status']['status']=='ok' and v['status']['guards_intact'] and v['status']['session_clean'] for v in r['runs'])
 out=ROOT/'refs/fixtures/olmradialblur_R08_fullsize_20261024';out.mkdir(parents=True,exist_ok=True)
 names={'polar':('pre_scatter','normalized_or_polar_rgba'),'source_scalar':('pre_scatter','slot_0x10'),'eligibility':('post_scatter_pre_gather','eligibility_mask'),'accum':('post_normalize','accum_rgba'),'max_alpha':('post_normalize','max_alpha'),'normalized':('post_normalize','normalized_or_polar_rgba')};stages={}
 for name,(stage,plane) in names.items():
  p=r['planes'][name];assert p['repeat_identical'] and p['different_bytes']==0 and p['original_sha256']==p['mac_sha256']
  a=zlib.decompress((S/'worker-R08-trace-1'/(name+'.zlib')).read_bytes());b=zlib.decompress((S/'worker-R08-trace-2'/(name+'.zlib')).read_bytes());mac=zlib.decompress((S/('mac-'+name+'.zlib')).read_bytes());assert a==b==mac and sha(a)==p['original_sha256'] and len(a)==p['bytes']
  filename=name+'.zlib';encoded=zlib.compress(a,9);(out/filename).write_bytes(encoded)
  stages.setdefault(stage,dict(stage=stage,planes={}))['planes'][plane]=dict(path=filename,raw_bytes=len(a),raw_sha256=sha(a),compressed_sha256=sha(encoded))
 (out/'manifest.json').write_text(json.dumps(dict(schema='olm-radial-fullsize-planes/R08',command_index=165,input_sha256=r['input_sha256'],runs=r['runs'],stages=list(stages.values()),scope='Six full-size planes only; existing independent sampler/writeback assertions unchanged'),indent=2)+'\n')
 p=ROOT/'tools/emulation/test_olmradialblur_case0010_rotation_mac_production_planes_20260805.py';text=p.read_text();old='refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805';new='refs/fixtures/olmradialblur_R08_fullsize_20261024';assert old in text or new in text;text=text.replace('FIXTURE = resolve_asset(ROOT / \"'+old+'\")','FIXTURE = resolve_asset(ROOT / \"'+new+'\")');text=text.replace('FULL_PF8_FIXTURE = FIXTURE / \"post_worker_full_pf8_argb.bin.zlib\"','FULL_PF8_FIXTURE = resolve_asset(ROOT / \"'+old+'/post_worker_full_pf8_argb.bin.zlib\")');p.write_text(text)
 print('refreshed six full-size plane pins; final/writer assertions preserved')
if __name__=='__main__':main()
