#!/usr/bin/env python3
"""Fail-closed discriminator for the remaining FUN_180001c90 Inner boundary."""
import hashlib,json,zlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
FIX=ROOT/'refs/fixtures/olmradialblur_rotation_pf16_inner32_small_20260806'
OUT=ROOT/'refs/conformance/olmradialblur_inner32_helper_discriminator_20260806.json'
def raw(n): return zlib.decompress((FIX/f'{n}.bin.zlib').read_bytes())
def arr(n,shape): return np.frombuffer(raw(n),'<f4').reshape(shape)
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 pre=arr('post_b150_pre_a9d0__accum_rgba',(9,1800,4)); post=arr('post_normalize__accum_rgba',(9,1800,4))
 m0=arr('post_b150_pre_a9d0__max_alpha',(9,1800)); m1=arr('post_normalize__max_alpha',(9,1800))
 changed=np.any(pre.view('<u4')!=post.view('<u4'),axis=2)
 max_changed=m0.view('<u4')!=m1.view('<u4'); first=tuple(int(x) for x in np.argwhere(max_changed)[0])
 rows=[]
 for r in range(9): rows.append({'radius':r,'changed_cells':int(np.count_nonzero(changed[r])),'delta_alpha_sum':float(np.sum(post[r,:,3]-pre[r,:,3],dtype=np.float64))})
 report={'kind':'olmradialblur_inner32_helper_discriminator_20260806','status':'actual_helper_replay_closed_portable_model_rejected','scope':'Offline actual-AEX pre/post plane discriminator plus captured first Inner helper direct replay; no production or AE claim','actual':{'pre_accum_sha256':sha(raw('post_b150_pre_a9d0__accum_rgba')),'post_accum_sha256':sha(raw('post_normalize__accum_rgba')),'pre_max_sha256':sha(raw('post_b150_pre_a9d0__max_alpha')),'post_max_sha256':sha(raw('post_normalize__max_alpha')),'first_max_store_change':{'radius':first[0],'angle':first[1],'before_bits':hex(int(m0[first].view('<u4'))),'after_bits':hex(int(m1[first].view('<u4'))),'before':float(m0[first]),'after':float(m1[first])},'rows':rows},'candidate_attempts':{'backward_next_row':{'accum_sha256':'44fdb158bab531d3c8b1f099a7837f82d0485c1c2561c6a2065951042d7821d2','max_sha256':'a43f0297e201a32e426a058a64e9b306de7f546a6b24753e586e27e6f79467c1','result':'rejected'},'forward_same_row':{'accum_sha256':'e9cb35dfaf588054d23af407c41e25b2b86451293231d0bf3a653fd40712264d','max_sha256':'1b7f99946c306846b32d4c774216b5294255aaea873370ddb8c6b12d8d3b8a28','result':'rejected'}},'direct_helper_replay':{'feasible':True,'direction':1,'return':'0x1800026ea','instructions':1012,'accum_exact':True,'max_exact':True,'fixture':'olmradialblur_rotation_pf16_inner32_small_actual_aex_20260806'},'classification':'The first actual Inner helper call now replays exactly from captured state. Both portable traversal candidates remain rejected; use the captured call to derive its store sequence before production promotion.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
