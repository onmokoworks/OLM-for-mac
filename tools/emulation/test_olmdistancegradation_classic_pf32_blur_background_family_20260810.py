#!/usr/bin/env python3
"""Execute the actual PF32 whole owner for blur/background/interpolation cells."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tools/emulation';PROBE=HERE/'probe_olmdistancegradation_pf32_owner_20260805.py';HARNESS=HERE/'dg_classic_pf32_blur_background_family_harness_20260810.cpp'
EXPECTED_BLUR={'constant.mode2':'f4696ac84b3cd30da637a7d2ebf965cb29e67256be66ada68b7d85ed9be4d21a','constant.mode3':'f67b7cbcdf3e5380c971f5ea91dd5a23da6c6a57527c468f8dcfe096d3b4989e','linear.mode2':'a664ac6185774955ed256cddc55a45b5161f07669ff16b5d3b53dc7a4ffab901','linear.mode3':'5666b13a5f368823107fb0af58a23d3f1dccde2b3457dc895c38d150f68236ec'}
EXPECTED_OUTPUT={'constant.mode2':'c71276a654368e18704799e9f19b35f345f3d45f6357814806e2ec929a1b753d','constant.mode3':'efe9cfc9932fc0f1f8e6d77e924eb0a9b8d227aad84a491bdd31071e1d736b9d','linear.mode2':'a79b3e5a478836128944d1c189ceb2a26b8457808e43ccc0ce58c17426b25e5d','linear.mode3':'b3c5dd901d494c54801438132bd202a31b959cf1c425cacbf2793205d7247f42'}
def main():
 cells={};blur_hashes={};field_hashes={};source_hashes=set()
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);exe=td/'h';src=td/'src';exp=td/'exp'
  q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(HERE/'dg_renderbits_real_harness_20260716'),str(HARNESS),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stderr
  for interp,iv in [('constant',1),('linear',2)]:
   for blur in (2,3):
    for bg in (0,1):
     env=os.environ.copy();env.update({'OLM_DG_PF32_SOURCE':'blur_family','OLM_DG_PF32_INTERP':str(iv),'OLM_DG_PF32_BG':str(bg),'OLM_DG_PF32_BLUR':str(blur),'OLM_DG_PF32_WRITE_ARTIFACTS':'0'})
     r=subprocess.run([str(HERE/'.venv/bin/python'),str(PROBE)],capture_output=True,text=True,env=env);assert r.returncode==0,r.stderr;p=json.loads(r.stdout[r.stdout.index('{'):]);assert p['status']=='owner_completed_field_captured' and p['failure'] is None and p['binary_sha256']=='a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae'
     o=p['output_world'];assert o['padding_unchanged'] and o['byte_count']==3168;source=bytes.fromhex(o['source_hex']);active=bytes.fromhex(o['active_hex']);expected=b''.join(active[y*17*16:(y+1)*17*16]+b'\xa5'*16 for y in range(11));assert hashlib.sha256(expected).hexdigest()==o['sha256']
     key=f'{interp}.mode{blur}.bg{bg}';cells[key]=o['active_sha256'];field_hashes[key]=p['intermediate_field']['sha256'];source_hashes.add(o['source_sha256'])
     returns=[x for x in p['matrix_captures'] if x['label']=='legacy_cvSmooth_blur' and x['phase']=='return'];assert len(returns)==1
     dst=returns[0]['args'][1];assert dst.get('active_sha256');blur_hashes[key]=dst['active_sha256']
     src.write_bytes(source);exp.write_bytes(expected);z=subprocess.run([str(exe),str(src),str(exp),interp,str(bg),str(blur)],capture_output=True,text=True);assert z.returncode==0,z.stderr;print(z.stdout,end='')
 assert source_hashes=={'7b321f71b74b40bb57965655b76ad00ee93d35073b6cf0d719fff336b88f8b9b'}
 for base,sha in EXPECTED_BLUR.items(): assert blur_hashes[base+'.bg0']==sha==blur_hashes[base+'.bg1']
 for base,sha in EXPECTED_OUTPUT.items(): assert cells[base+'.bg0']==sha==cells[base+'.bg1']
 assert len(set(blur_hashes.values()))==4 and len(set(cells.values()))==4
 print('source_sha256',next(iter(source_hashes)));print('field_sha256',field_hashes);print('blurred_sha256',blur_hashes);print('output_sha256',cells);print('PASS_OLMDISTANCEGRADATION_CLASSIC_PF32_BLUR_BACKGROUND_FAMILY_EXACT')
if __name__=='__main__':raise SystemExit(main())
