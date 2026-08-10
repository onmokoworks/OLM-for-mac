#!/usr/bin/env python3
"""Compare actual exported Distance Smart owner against bounded production evidence."""
from __future__ import annotations
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
AEX=ROOT/'aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex'
PF8_EVIDENCE=ROOT/'refs/conformance/olmdistancegradation_classic_pf8_blur_background_family_exact_20260810.json'
REPORT=ROOT/'refs/conformance/olmdistancegradation_exported_upstream_owner_seam_20260811.json'
DOC=REPORT.with_suffix('.md')
DEFAULT_WORKER=Path('/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker')
BASE=['Invert=1','In/Out=1','Inside Threshold=4','Outside Threshold=4','Render Mode=1','Gradation Color=255,28,0,238','BG Color =255,16,160,48','Power=1','Blur Size=1']
DEPTH_FAILURE='guest called _CxxThrowException outside the supported selector-abort contract (msvc_type=.H)'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def params(interp,blur,bg): return [*BASE,f'Use Background Color={bg}',f'Interpolation Mode={1 if interp=="constant" else 2}',f'Blur Mode={blur}']
def run(worker,source,output,fmt,values):
 return subprocess.run([str(worker),'render-png',str(AEX),str(source),str(output),'--pixel-format',fmt,*values],text=True,capture_output=True,timeout=20)

def main():
 worker=Path(os.environ.get('OLM_AEX_GUEST_WORKER',str(DEFAULT_WORKER)))
 if not worker.is_file(): raise RuntimeError(f'AEXCompat worker missing: {worker}')
 expected={(r['interpolation'],r['blur_mode'],int(r['use_background'])):r['output_active_sha256'] for r in json.loads(PF8_EVIDENCE.read_text())['rows']}
 rows=[];depth_boundaries=[]
 with tempfile.TemporaryDirectory(prefix='dg_exported_owner_') as td:
  td=Path(td);source=td/'input.png';image=Image.new('RGBA',(17,11));image.putdata([((x*613+y*1231)%256,(x*997+y*211)%256,(x*1499+y*307)%256,255) if not (4<=x<13 and 2<=y<9) else (0,0,0,0) for y in range(11) for x in range(17)]);image.save(source);input_sha=sha(source)
  for interp in ('constant','linear'):
   for blur in (2,3):
    for bg in (0,1):
     result=run(worker,source,td/f'pf8_{interp}_{blur}_{bg}.png','argb8',params(interp,blur,bg));assert result.returncode==0,result.stderr;payload=json.loads(result.stdout);want=expected[interp,blur,bg]
     assert payload['raw_pixel_bytes']==748
     assert payload['gpu']['pre_render']['completed'] and payload['gpu']['render']['completed'] and payload['gpu']['cleanup_complete']
     assert not payload['unsupported_suite_calls'] and payload['render_error']==0
     rows.append({'depth':'PF8','interpolation':interp,'blur_mode':blur,'use_background':bool(bg),'actual_exported_raw_sha256':payload['raw_pixel_sha256'],'production_whole_chain_active_sha256':want,'bytes_compared':748,'exact':payload['raw_pixel_sha256']==want})
  for depth,fmt in (('PF16','argb16'),('PF32','argb32f')):
   result=run(worker,source,td/f'{depth}.png',fmt,params('constant',2,0));assert result.returncode!=0;payload=json.loads(result.stdout);assert DEPTH_FAILURE in payload['error'];assert payload['gpu']['pre_render']['completed'] and payload['gpu']['render']['attempted'] and not payload['gpu']['render']['completed'] and payload['gpu']['cleanup_complete']
   depth_boundaries.append({'depth':depth,'pixel_format':fmt,'representative':'constant.mode2.bg0','error':payload['error'],'smart_pre_render':payload['gpu']['pre_render'],'smart_render':payload['gpu']['render']})
 assert all(r['exact'] for r in rows)
 report={'schema':'olmdistancegradation.exported-upstream-owner-seam/2','status':'PASS_PF8_EXPORTED_SMART_OWNER_8_CELL_EXACT_PF16_PF32_EXCEPTION_BOUNDARY','actual_aex_sha256':sha(AEX),'aexcompat_worker':{'path':str(worker),'sha256':sha(worker),'modified_by_olm_task':False},'fixture':{'width':17,'height':11,'input_png_sha256':input_sha},'exported_pf8_rows':rows,'depth_boundaries':depth_boundaries,'numerical_family_already_exact':{'cells':24,'product':'PF8/PF16/PF32 x Constant/Linear x Blur2/3 x Background off/on','evidence':['refs/conformance/olmdistancegradation_classic_pf8_blur_background_family_exact_20260810.md','refs/conformance/olmdistancegradation_classic_pf16_blur_background_family_exact_20260810.md','refs/conformance/olmdistancegradation_classic_pf32_blur_background_family_exact_20260810.md']},'load_library_w_trace':{'requested_in_order':[r'C:\AEXCompat\opencv_core_parallel_onetbb455_64.dll','opencv_core_parallel_onetbb455_64.dll',r'C:\AEXCompat\opencv_core_parallel_tbb455_64.dll','opencv_core_parallel_tbb455_64.dll',r'C:\AEXCompat\opencv_core_parallel_openmp455_64.dll','opencv_core_parallel_openmp455_64.dll'],'resolution':'all absent -> NULL + ERROR_MOD_NOT_FOUND -> OpenCV built-in fallback','success_path_symbol':'opencv_core_parallel_plugin_init_v0','external_pe_mapping':False},'linear_residual_localization':{'parameter_materialization':'exact in worker report: RGB, inside threshold 4, interpolation 2, power 1, requested background and blur values','field_and_blur':'green lane/output alpha equals the existing fieldgen+blur staged matrix','first_difference':'compose auxiliary red lane was zero in production/manual staging but equals blurred X in the actual owner','fix':'stage blurred X as PF8 Linear+blur field_aux and preserve it in zero-ownership RGB compose','four_complete_buffers_exact_after_fix':True},'owner_facts':{'PF8':'actual exported SmartPreRender/SmartRender completes all 8 cells and matches production whole-chain active bytes','PF16':'exported Smart owner throws before output; classic/helper numerical 8 cells remain exact separately','PF32':'actual AEX has no SmartRender PF32 branch; classic whole owner FUN_181172a10 numerical 8 cells remain exact separately'},'claims_not_made':['No PF16 exported owner equality','No PF32 SmartRender route or equality','No native After Effects execution','No external OpenCV backend PE loading']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 DOC.write_text('# OLMDistanceGradation exported upstream owner seam\n\nStatus: **'+report['status']+'**.\n\nThe unchanged Windows AEX now completes exported SmartPreRender/SmartRender for the full PF8 Constant/Linear × Blur 2/3 × Background off/on product. All eight 17×11 tight buffers match the production whole chain byte-for-byte. The six optional OpenCV 4.5.5 parallel backend DLL candidates are absent, return `NULL + ERROR_MOD_NOT_FOUND`, and correctly fall back to the built-in backend.\n\nThe former Linear-only residual was localized after field generation and blur: the green lane and output alpha already matched, while production/manual staging left the compose auxiliary red lane at zero. The actual owner stages blurred `X` into that lane too. Production now passes blurred `X` as PF8 Linear+blur `field_aux` and preserves it in the zero-ownership RGB branches, closing all four complete buffers.\n\nPF16 and PF32 representative exported Smart runs stop in the actual AEX through `_CxxThrowException` before output. This does not invalidate their separately exact eight-cell numerical evidence: PF16 is covered through the fieldgen/blur/typed-compose chain, and PF32 through classic whole owner `FUN_181172a10`. The actual AEX has no PF32 SmartRender branch. No external PE was loaded and no native AE execution is claimed.\n')
 print(report['status'])
if __name__=='__main__':raise SystemExit(main())
