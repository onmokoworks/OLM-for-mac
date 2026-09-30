#!/usr/bin/env python3
"""Legal Thin: exported AEX Smart owner versus real-SDK Mac Classic/Smart.

The worker executable is explicitly supplied and hashed; no historical worker
identity or installed/native AE claim is inherited. Raw images stay temporary.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from PIL import Image
import probe_olmcolorkey_composition_generalization_20261001 as general
import probe_olmcolorkey_composition_hypotheses_20261001 as hypotheses

ROOT = general.ROOT
SDK_PROBE = ROOT / "tools/emulation/colorkey_thin_public_host_20261001.hpp"
HARNESS = r'''
int main(int argc,char**argv) {
 if(argc!=8)return 90;
 int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]),thin=atoi(argv[4]);
 int distance=atoi(argv[5]),keep=atoi(argv[6]),route=atoi(argv[7]);
 int ps=depth==8?4:depth==16?8:16,rb=w*ps+8;
 std::vector<std::uint8_t>ib((size_t)rb*h),ob((size_t)rb*h,0xee);
 if(fread(ib.data(),1,ib.size(),stdin)!=ib.size())return 91;
 auto before=ib;
 OLMColorKeyInfo info{};
 info.color_keep=keep;info.number_of_colors=2;
 info.use_color[0]=info.use_color[1]=true;
 info.colors8[0]={255,0,0,0};info.colors8[1]={255,0,255,0};
 info.colors[0]={1,0,0,0};info.colors[1]={1,0,1,0};
 info.edge_thin_amount=thin;info.edge_thin_distance_type=distance;
 info.edge_blur_distance_type=2;info.edge_blur_direction=102;
 PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS]={};PF_ParamDef*params[OLMCOLORKEY_NUM_PARAMS]={};
 FillParams(info,defs,params);
 auto in=MakeWorld(ib,rb,w,h),out=MakeWorld(ob,rb,w,h);
 defs[OLMCOLORKEY_INPUT].u.ld=in;
 HostState state;state.input=&in;state.output=&out;state.params=defs;
 state.format=depth==8?PF_PixelFormat_ARGB32:depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;
 g_host=&state;
 SPBasicSuite basic={};basic.AcquireSuite=Acquire;basic.ReleaseSuite=Release;
 auto in_data=MakeInData(&state,&basic);PF_OutData out_data={};PF_Err err=0;
 if(!route)err=EffectMain(PF_Cmd_RENDER,&in_data,&out_data,params,&out,NULL);
 else {
  PF_PreRenderInput pi={};PF_PreRenderOutput po={};PF_PreRenderCallbacks pc={};pc.checkout_layer=CheckoutLayer;
  PF_PreRenderExtra pe={&pi,&po,&pc};
  err=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in_data,&out_data,NULL,NULL,&pe);
  if(err)return 92;
  PF_SmartRenderInput si={};si.bitdepth=depth;PF_SmartRenderCallbacks sc={};
  sc.checkout_layer_pixels=CheckoutPixels;sc.checkin_layer_pixels=CheckinPixels;sc.checkout_output=CheckoutOutput;
  PF_SmartRenderExtra se={&si,&sc};
  err=EffectMain(PF_Cmd_SMART_RENDER,&in_data,&out_data,NULL,NULL,&se);
  if(state.pre!=1||state.layer!=1||state.output_checkout!=1||state.layer_checkin!=1||
     state.param_checkout!=33||state.param_checkin!=33||state.preserve)return 93;
 }
 if(err||ib!=before||state.acquire!=2||state.release!=2||state.world_calls!=2||state.color_calls!=4)return 94;
 for(int y=0;y<h;y++) {
  for(int b=w*ps;b<rb;b++)if(ob[(size_t)y*rb+b]!=0xee)return 95;
  if(fwrite(ob.data()+(size_t)y*rb,1,(size_t)w*ps,stdout)!=(size_t)w*ps)return 96;
 }
 return 0;
}
'''

def compile_public(directory: Path, body: str) -> Path:
    directory.mkdir()
    modified=directory/"OLMColorKey.cpp"
    modified.write_text(body.replace('#include "OLMColorKey.h"',
                         '#include "'+str(general.SOURCE.with_suffix('.h'))+'"'))
    source=directory/"public.cpp"
    source.write_text(SDK_PROBE.read_text().replace(
        '#include "../../mac/OLMColorKey/OLMColorKey.cpp"','#include "'+str(modified)+'"').replace(
        'int main()', 'int legacy_main()')+HARNESS)
    sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
    exe=directory/"public"
    subprocess.run(['clang++','-std=c++17','-arch','arm64','-O2','-fno-fast-math','-ffp-contract=off',
        '-Wno-pragma-pack','-Wno-deprecated-declarations','-isysroot',sdk,'-IHeaders','-IHeaders/SP',
        '-IUtil','-IResources','-Imac/OLMColorKey',str(source),'mac/OLMColorKey/OLMColorKey_Strings.cpp',
        'Util/AEGP_SuiteHandler.cpp','Util/MissingSuiteError.cpp','-framework','Cocoa','-o',str(exe)],
        cwd=ROOT,check=True,capture_output=True)
    return exe

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',type=Path,required=True)
    parser.add_argument('--production',action='store_true')
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    original=general.SOURCE.read_text()
    candidate=original if args.production else hypotheses.kernel_variants(original)['native_final_complement'].replace(
        'info.edge_thin_amount != 0.0 || info.edge_blur_amount != 0.0','info.edge_thin_amount != 0.0',3).replace(
        'const float scale = OLMCKPixelTraits<PixelT>::is_32bpc() ? 1.0f : 255.0f;',
        'const float scale = 1.0f;').replace(
        'const float distance_scale = OLMCKPixelTraits<PixelT>::is_32bpc() ? 1.0f : 255.0f;',
        'const float distance_scale = 1.0f;')
    sha=general.base.sha
    worker_digest=sha(args.worker.read_bytes())
    aex=general.base.retained.actual_probe.AEX
    rows=[]
    with tempfile.TemporaryDirectory(prefix='olmck_thin_owner_') as raw:
        directory=Path(raw);exe=compile_public(directory/'mac',candidate)
        for fixture in general.FIXTURES:
            w,h=fixture['width'],fixture['height']
            raw8,rb8=general.fixture(fixture,'PF8')
            image=Image.new('RGBA',(w,h))
            image.putdata([tuple(raw8[y*rb8+x*4+1:y*rb8+x*4+4])+(raw8[y*rb8+x*4],)
                           for y in range(h) for x in range(w)])
            input_png=directory/'input.png';image.save(input_png)
            for keep in (False,True):
                for distance in (1,2,3):
                    for thin in (-4,-1,1,4):
                        for depth,fmt in (('PF8','argb8'),('PF16','argb16'),('PF32','argb32f')):
                            params=[f'Color Keep={int(keep)}','Premultiplied Color=0','Number of Colors=2',
                                'Use Color 1=1','Color 1=255,0,0,0','Use Color 2=1','Color 2=255,0,255,0',
                                f'Amount@14={thin}',f'Distance Type@15={distance}']
                            actual=json.loads(subprocess.check_output([str(args.worker),'render-png',str(aex),
                                str(input_png),str(directory/'output.png'),'--pixel-format',fmt,*params],text=True))
                            if (actual['render_error'] or not actual['guards_intact'] or
                                actual['unsupported_suite_calls'] or actual['dropped_unsupported_suite_calls'] or
                                actual['setup']['global_setup_error'] or actual['setup']['params_setup_error']):
                                raise RuntimeError('exported owner execution failure')
                            values={p['slot']:p.get('value') for p in actual['parameter_values']}
                            if values[1]!=int(keep) or values[14]!=thin or values[15]!=distance:
                                raise RuntimeError('legal parameter propagation drift')
                            source,rb=general.fixture(fixture,depth)
                            results={}
                            for route,name in ((0,'classic'),(1,'smart')):
                                output=subprocess.check_output([str(exe),str(w),str(h),depth[2:],str(thin),
                                                                str(distance),str(int(keep)),str(route)],input=source)
                                if len(output)!=actual['raw_pixel_bytes']:raise RuntimeError('output size drift')
                                digest=sha(output)
                                results[name]={'exact':digest==actual['raw_pixel_sha256'],'sha256':digest}
                            rows.append({'fixture':fixture,'keep':keep,'thin':thin,'type':distance,'depth':depth,
                                'input_sha256':sha(source),'input_png_sha256':actual['input_png_sha256'],
                                'actual_sha256':actual['raw_pixel_sha256'],'parameter_values':actual['parameter_values'],
                                'guards_intact':actual['guards_intact'],'results':results})
                    print(f"{fixture['id']} keep={keep} type={distance}",flush=True)
    report={'schema':'olmcolorkey.thin-public-owner/1','date':'2026-10-01','case_count':len(rows),
        'production':args.production,'source_sha256':sha(original.encode()),'candidate_source_sha256':sha(candidate.encode()),
        'worker_sha256':worker_digest,'aex_sha256':sha(aex.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),
        'dependencies':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in
                        (SDK_PROBE,Path(general.__file__),Path(hypotheses.__file__),general.SOURCE.with_suffix('.h'))},
        'summary':{route:sum(r['results'][route]['exact'] for r in rows) for route in ('classic','smart')},
        'cases':rows,'scope':'Exported AEX Smart CPU owner with actual parameter builder; real SDK Mac Classic/Smart callbacks. PNG RGBA8 promoted to typed pixels; no native Windows AE or installed binary claim.'}
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report['summary']))
    return 0

if __name__=='__main__':raise SystemExit(main())
