#!/usr/bin/env python3
"""Verify the bounded exported Smart owner evidence across all depths."""
import hashlib, json, os, subprocess, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
AEX=ROOT/'aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex'
PF8_EVIDENCE=ROOT/'refs/conformance/olmdistancegradation_classic_pf8_blur_background_family_exact_20260810.json'
TYPED_EVIDENCE=ROOT/'refs/conformance/olmdistancegradation_exported_typed_owner_matrix_20260811.json'
REPORT=ROOT/'refs/conformance/olmdistancegradation_exported_upstream_owner_seam_20260811.json';DOC=REPORT.with_suffix('.md')
DEFAULT_WORKER=Path('/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker')
BASE=['Invert=1','In/Out=1','Inside Threshold=4','Outside Threshold=4','Render Mode=1','Gradation Color=255,28,0,238','BG Color =255,16,160,48','Power=1','Blur Size=1']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def params(interp,blur,bg):return [*BASE,f'Use Background Color={bg}',f'Interpolation Mode={1 if interp=="constant" else 2}',f'Blur Mode={blur}']
def main():
 worker=Path(os.environ.get('OLM_AEX_GUEST_WORKER',str(DEFAULT_WORKER)));assert worker.is_file()
 expected={(r['interpolation'],r['blur_mode'],int(r['use_background'])):r['output_active_sha256'] for r in json.loads(PF8_EVIDENCE.read_text())['rows']};rows=[]
 with tempfile.TemporaryDirectory(prefix='dg_exported_owner_') as td:
  td=Path(td);source=td/'input.png';image=Image.new('RGBA',(17,11));image.putdata([((x*613+y*1231)%256,(x*997+y*211)%256,(x*1499+y*307)%256,255) if not (4<=x<13 and 2<=y<9) else (0,0,0,0) for y in range(11) for x in range(17)]);image.save(source);input_sha=sha(source)
  for interp in ('constant','linear'):
   for blur in (2,3):
    for bg in (0,1):
     result=subprocess.run([str(worker),'render-png',str(AEX),str(source),str(td/f'{interp}_{blur}_{bg}.png'),'--pixel-format','argb8',*params(interp,blur,bg)],text=True,capture_output=True,timeout=20);assert result.returncode==0,result.stderr;payload=json.loads(result.stdout);want=expected[interp,blur,bg]
     rows.append({'depth':'PF8','interpolation':interp,'blur_mode':blur,'use_background':bool(bg),'actual_exported_raw_sha256':payload['raw_pixel_sha256'],'production_whole_chain_active_sha256':want,'bytes_compared':748,'exact':payload['raw_pixel_sha256']==want})
 assert all(r['exact'] for r in rows)
 typed=json.loads(TYPED_EVIDENCE.read_text());assert typed['status']=='PASS_PF16_PF32_EXPORTED_SMART_OWNER_16_CELL_EXACT'
 report={'schema':'olmdistancegradation.exported-upstream-owner-seam/3','status':'PASS_EXPORTED_SMART_OWNER_ALL_DEPTHS_BOUNDED_EXACT','actual_aex_sha256':sha(AEX),'aexcompat_worker':{'path':str(worker),'sha256':sha(worker),'modified_by_olm_task':False},'fixture':{'width':17,'height':11,'input_png_sha256':input_sha},'exported_pf8_rows':rows,'typed_owner_evidence':{'path':str(TYPED_EVIDENCE.relative_to(ROOT)),'status':typed['status'],'summary':typed['summary']},'owner_facts':{'PF8':'exported Smart owner 8/8 exact','PF16':'exported Smart owner 8/8 exact; classic owner remains separately exact','PF32':'exported Smart owner 8/8 exact; classic FUN_181172a10 remains separately exact'},'claims_not_made':['No native After Effects execution','No Mac partial-world/origin claim']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 DOC.write_text('# OLMDistanceGradation exported upstream owner seam\n\nStatus: **'+report['status']+'**.\n\nThe unchanged Windows AEX completes the bounded exported Smart owner matrix at PF8, PF16, and PF32. PF8 contributes eight exact cells; the typed-owner evidence contributes eight PF16 and eight PF32 exact cells.\n\nClassic PF16 and classic PF32 remain distinct, separately exact owners. Mac PF32 Smart admission and full-frame field generation have focused source-included adapter evidence; native AE and partial-world origin behavior remain separate boundaries.\n')
 print(report['status'])
if __name__=='__main__':raise SystemExit(main())
