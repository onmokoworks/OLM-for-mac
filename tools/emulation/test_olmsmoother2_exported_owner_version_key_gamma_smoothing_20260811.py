#!/usr/bin/env python3
"""Actual exported SmartRender owner versus production on the compound 5x5 fixture."""
from __future__ import annotations
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
AEX=ROOT/'aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex'
SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
ASM=ROOT/'disasm/OLMSmoother2.aex.asm.txt'
HARNESS=ROOT/'tools/emulation/olmsmoother2_version_key_gamma_smoothing_production_harness_20260810.cpp'
REPORT=ROOT/'refs/conformance/olmsmoother2_exported_owner_version_key_gamma_smoothing_20260811.json'
DOC=ROOT/'refs/conformance/olmsmoother2_exported_owner_version_key_gamma_smoothing_20260811.md'
AEX_SHA='7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7'
DEFAULT_WORKER=Path('/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker')
RGB=[(1,1,1),(255,0,0),(65,1,1),(0,255,0),(206,55,161),(86,55,26),(43,73,217),(231,16,235),(116,106,230),(1,9,43),(91,38,34),(99,183,84),(230,125,149),(208,155,60),(168,21,161),(233,157,226),(8,57,119),(159,56,196),(232,156,109),(50,140,246),(229,135,20),(36,6,46),(176,107,229),(168,83,193),(235,7,162)]
CASES=[(1,False),(2,True)]
DEPTHS={'PF8':('argb8',4,5),'PF16':('argb16',8,7),'PF32':('argb32f',16,13)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2_owner_prod_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True,capture_output=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return {k:bytes.fromhex(v) for k,v in (line.split() for line in o.splitlines())}
def tight(raw,depth):
 _fmt,ps,pad=DEPTHS[depth];rb=5*ps+pad
 return b''.join(raw[y*rb:y*rb+5*ps] for y in range(5))
def params(version,invert):
 return ['Enable Color Key=1','Color Key=255,1,1,1',f'Invert Color Key={int(invert)}','Smoothness=100','Extra Smooth=100','Smooth Range=100',f'Smoother Version={version}','Gamma Correction=2','Gamma Value=2.4','Number of Gamma Colors=2','Gamma Color@11=255,255,0,0','Gamma Color@12=255,1,1,1']
def asm_owner_contract():
 text=ASM.read_text();render=text[text.index('; === FUN_180005c30'):text.index('; === FUN_180005c40')]
 req('XOR EAX,EAX' in render and 'RET' in render,'legacy Render no-op drift')
 return {'exported_entry':'0x180009e60','command_dispatch':{'PF_Cmd_RENDER_11':'0x180005c30 (xor eax,eax; ret)','PF_Cmd_SMART_PRE_RENDER_23':'vtable +0x10 = 0x180005620','PF_Cmd_SMART_RENDER_24':'vtable +0x20 = 0x180001f10'},'smart_render_materialization':'PF_InData checkout_param/checkin_param callbacks feed FUN_180004e10 before bitdepth 8/16/32 dispatch','asm_sha256':sha(ASM)}
def main():
 req(sha(AEX)==AEX_SHA,'AEX hash drift');worker=Path(os.environ.get('OLM_AEX_GUEST_WORKER',str(DEFAULT_WORKER)));req(worker.is_file(),'AEXCompat worker missing');prod=production();rows=[]
 with tempfile.TemporaryDirectory(prefix='sm2_owner_') as td:
  td=Path(td);inp=td/'input.png';im=Image.new('RGBA',(5,5));im.putdata([(*p,255) for p in RGB]);im.save(inp);input_sha=hashlib.sha256(inp.read_bytes()).hexdigest()
  for depth,(fmt,ps,_pad) in DEPTHS.items():
   for version,invert in CASES:
    variant=f'v{version}_{"invert" if invert else "noninvert"}';out=td/f'{depth}_{variant}.png';cmd=[str(worker),'render-png',str(AEX),str(inp),str(out),'--pixel-format',fmt,*params(version,invert)];p=subprocess.run(cmd,text=True,capture_output=True,check=True);a=json.loads(p.stdout);expected=tight(prod[f'{depth}_{variant}'],depth);expected_sha=hashlib.sha256(expected).hexdigest()
    req(a['render_error']==0,depth+' '+variant+' render error');req(a['raw_pixel_bytes']==25*ps,depth+' '+variant+' raw size');req(a['raw_pixel_sha256']==expected_sha,depth+' '+variant+' raw mismatch');req(not a['unsupported_suite_calls'] and a['dropped_unsupported_suite_calls']==0,depth+' '+variant+' unsupported suite');req(a['gpu']['pre_render']['completed'] and a['gpu']['pre_render']['error']==0 and a['gpu']['render']['completed'] and a['gpu']['render']['error']==0,depth+' '+variant+' smart owner incomplete')
    rows.append({'depth':depth,'pixel_format':fmt,'version':version,'key_polarity':'invert' if invert else 'non-invert','actual_exported_raw_bytes':a['raw_pixel_bytes'],'actual_exported_raw_sha256':a['raw_pixel_sha256'],'production_tight_raw_sha256':expected_sha,'smart_pre_render':a['gpu']['pre_render'],'smart_render':a['gpu']['render'],'render_mode':a['render_mode'],'suite_requests':a['suite_requests'],'unsupported_suite_calls':a['unsupported_suite_calls'],'parameter_values':a['parameter_values'],'exact':True})
 report={'schema':'olmsmoother2.exported-owner-compound/1','verdict':'PASS_ACTUAL_EXPORTED_SMART_OWNER_VERSION_KEY_GAMMA_SMOOTHING_ALL_DEPTHS_EXACT','scope':'actual unchanged Windows AEX exported SmartPreRender/SmartRender complete tight buffers versus production RenderBits; 5x5 RGBA8 source promoted by host to PF8/PF16/PF32; Version1 non-invert and Version2 invert representatives; Gamma Colors [red,key] 2.4; Smoothness/Range/Extra100','actual_aex_sha256':AEX_SHA,'aexcompat_worker':{'path':str(worker),'sha256':sha(worker),'modified_by_this_task':False},'owner_contract':asm_owner_contract(),'host_callback_abi_reached':['PF Handle Suite v2 global_data owner','PF_InData checkout_param/checkin_param materialization','SmartPreRender checkout_layer','SmartRender checkout_layer_pixels and checkout_output','PF World Suite v2 ARGB8/ARGB16/ARGB32F primary worlds','PF ColorParamSuite v1 colors','VCOMP static/dynamic/fork single-thread scheduling'],'fixture':{'width':5,'height':5,'source_rgba8_sha256':input_sha,'rgb_u8':[list(x) for x in RGB],'row_padding':'actual exported owner tight; production padding stripped only for equality comparison'},'cases':rows,'production_source_sha256':sha(SOURCE),'claims_not_made':['No arbitrary parameter products or geometry','No native Windows execution in this task','No After Effects host/color-management execution','The July legacy_case_0012 Mac-AE residual is not superseded by this 5x5 owner fixture']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 actual exported owner seam\n\nVerdict: `'+report['verdict']+'`\n\nThe unchanged Windows AEX exported `SmartPreRender`/`SmartRender` owner materializes the compound parameters and produces complete tight PF8, PF16, and PF32 buffers. Version 1 + non-invert key and Version 2 + invert key representatives match production `RenderBits` byte-for-byte (float-bit-for-float-bit for PF32). All six runs complete with no unsupported suite calls.\n\nThe legacy `PF_Cmd_RENDER` dispatch target is a literal success no-op; the numerical public owner is Smart Render. Required callbacks exercised here are the global PF Handle owner, parameter checkout/checkin, Smart checkout callbacks, PF World Suite typed primary worlds, ColorParamSuite, and VCOMP scheduling. AEXCompat was used read-only and was not modified.\n\nThis focused 5x5 owner fixture does not supersede the July `legacy_case_0012` Mac-AE host residual.\n');print(report['verdict'])
if __name__=='__main__':raise SystemExit(main())
