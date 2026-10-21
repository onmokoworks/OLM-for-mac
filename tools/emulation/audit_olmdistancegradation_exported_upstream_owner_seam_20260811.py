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
 typed=json.loads(TYPED_EVIDENCE.read_text());assert typed['status']=='PASS_56_ADMITTED_RAW_EXACT_8_PF32_POWER_FAIL_CLOSED'
 assert typed['summary']=={'actual_aex_cells':64,'exact_admitted':56,'pf16_exact':32,'pf32_exact':24,'pf32_power_fail_closed':8,'pf32_mode5_exact':6,'pf32_mode5_fail_closed':2}
 report={'schema':'olmdistancegradation.exported-upstream-owner-seam/5','status':'PASS_EXPORTED_SMART_OWNER_ALL_DEPTHS_BOUNDED_64_RAW_EXACT_8_POWER_FAIL_CLOSED','actual_aex_sha256':sha(AEX),'aexcompat_worker':{'path':str(worker),'sha256':sha(worker),'modified_by_olm_task':False},'fixture':{'width':17,'height':11,'input_png_sha256':input_sha},'exported_pf8_rows':rows,'typed_owner_evidence':{'path':str(TYPED_EVIDENCE.relative_to(ROOT)),'status':typed['status'],'summary':typed['summary']},'owner_facts':{'PF8':'exported Smart owner 8/8 exact in this bounded upstream subset','PF16':'exported Smart owner 32/32 exact on the fixed typed matrix; classic owner remains separately exact','PF32':'actual public Smart owner has 24 admitted non-Power exact cells; eight Power cells fail closed pending native Windows UCRT powf capture'},'claims_not_made':['No native After Effects execution','No native Windows UCRT powf result for PF32 Power','No Mac partial-world/origin claim','No unlisted PF32 tuple, geometry, or layout claim']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 DOC.write_text(
  '# OLMDistanceGradation exported upstream owner seam\n\n'
  'Status: **'+report['status']+'**.\n\n'
  'The unchanged Windows AEX has exported Smart owners at PF8, PF16, and PF32.\n'
  'This audit contributes eight exact PF8 upstream cells; the current fixed 17x11\n'
  'typed matrix contributes 32 exact PF16 cells plus 24 admitted non-Power PF32 cells.\n'
  'Eight PF32 Power cells fail closed pending a native Windows UCRT powf capture.\n\n'
  'The earlier 16-cell/all-exact summary is superseded. The actual public PF32\n'
  'Smart owner exists; production admission remains bounded to the recorded\n'
  'matrix. Classic PF16 and PF32 remain distinct, separately exact owners. Native\n'
  'AE, partial-world origin, and unlisted tuple/geometry/layout behavior remain\n'
  'separate boundaries.\n')
 print(report['status'])
if __name__=='__main__':raise SystemExit(main())
