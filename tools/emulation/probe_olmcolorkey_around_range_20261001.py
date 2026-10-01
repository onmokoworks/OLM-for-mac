#!/usr/bin/env python3
"""Recover Around across legal Blur amounts/metrics with the exported owner."""
import argparse,json,subprocess,tempfile
from pathlib import Path
from PIL import Image
import probe_olmcolorkey_around_composition_owner_20261001 as around
thin_owner=around.thin_owner
ROOT=around.ROOT
SOURCE=around.SOURCE
sha=thin_owner.general.base.sha
HARNESS=around.HARNESS.replace('if(argc!=11)','if(argc!=12)').replace('info.edge_blur_amount=atoi(argv[8]);','info.edge_blur_amount=atof(argv[8]);').replace('info.edge_blur_distance_type=2;info.edge_blur_direction=102;', 'info.edge_blur_distance_type=atoi(argv[11]);info.edge_blur_direction=102;').replace('FillParams(info,defs,params);','FillParams(info,defs,params);\n if(defs[OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE].u.pd.value!=atoi(argv[11]) ||\n    defs[OLMCOLORKEY_EDGE_BLUR_AMOUNT].u.fs_d.value!=atof(argv[8]))return 98;').replace('if(err||ib!=before||','if(ib!=before||').replace(' for(int y=0;y<h;y++) {\n  for(int b=w*ps;', ''' fprintf(stderr,"ERROR %d\\n",int(err));
 if(err) {for(auto value:ob)if(value!=0xee)return 97;return 0;}
 for(int y=0;y<h;y++) {
  for(int b=w*ps;''')

def candidate_source(body):
    old='return info.edge_blur_direction == 102 && info.edge_blur_distance_type == 2 &&\n\t\t   info.edge_blur_amount == 4.0;'
    new='return info.edge_blur_direction == 102 && info.edge_blur_distance_type >= 1 &&\n           info.edge_blur_distance_type <= 3 && std::isfinite(info.edge_blur_amount) &&\n           info.edge_blur_amount > 0.0 && info.edge_blur_amount <= 4000.0;'
    assert body.count(old)==1
    body=body.replace(old,new)
    old='const bool use_pf32_amount2_native_plane =\n\t\t    OLMCKPixelTraits<PixelT>::is_32bpc()'
    assert body.count(old)==1
    return body.replace(old,'const bool use_pf32_amount2_native_plane =\n            !IsRecoveredAroundBlur(info) && OLMCKPixelTraits<PixelT>::is_32bpc()')

def compile_public(directory,body,sanitize=False):
    saved=thin_owner.HARNESS
    try:thin_owner.HARNESS=HARNESS;exe=thin_owner.compile_public(directory,body)
    finally:thin_owner.HARNESS=saved
    if sanitize:
        sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
        subprocess.run(['clang++','-std=c++17','-arch','arm64','-O1','-g','-fno-fast-math','-ffp-contract=off','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Wno-pragma-pack','-Wno-deprecated-declarations','-isysroot',sdk,'-IHeaders','-IHeaders/SP','-IUtil','-IResources','-Imac/OLMColorKey',str(directory/'public.cpp'),'mac/OLMColorKey/OLMColorKey_Strings.cpp','Util/AEGP_SuiteHandler.cpp','Util/MissingSuiteError.cpp','-framework','Cocoa','-o',str(exe)],cwd=ROOT,check=True,capture_output=True)
    return exe

def mac_render(exe,fixture,depth,thin,thin_type,keep,route,blur,premultiplied,replace,blur_type,env=None):
    source,_=around.source_fixture(fixture,depth)
    run=subprocess.run([str(exe),str(fixture['width']),str(fixture['height']),depth[2:],str(thin),str(thin_type),str(int(keep)),str(route),str(blur),str(int(premultiplied)),str(int(replace)),str(blur_type)],input=source,check=True,capture_output=True,env=env)
    err=int(run.stderr.decode().strip().split(' ')[1]);assert not err or not run.stdout
    return err,run.stdout

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--candidate',action='store_true');ap.add_argument('--full',action='store_true');ap.add_argument('--boundaries',action='store_true');ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    original=SOURCE.read_text();body=candidate_source(original) if args.candidate else original;rows=[]
    fixtures=thin_owner.general.FIXTURES if args.full else thin_owner.general.FIXTURES[2:3]
    if args.boundaries:fixtures=({'id':'single_opaque','width':1,'height':1,'alpha':'opaque'},{'id':'column_opaque','width':1,'height':7,'alpha':'opaque'},{'id':'row_mixed_zero','width':9,'height':1,'alpha':'mixed'})
    amounts=(.1,.5,1,1.5,2,4,7.3,31.5,100,4000)
    toggles=((False,False),(False,True),(True,False),(True,True)) if args.full else ((False,False),)
    aex=thin_owner.general.base.retained.actual_probe.AEX
    with tempfile.TemporaryDirectory(prefix='olmck_around_range_') as td:
        temp=Path(td);exe=compile_public(temp/'mac',body)
        for fixture in fixtures:
            w,h=fixture['width'],fixture['height'];raw8,rb=around.source_fixture(fixture,'PF8');im=Image.new('RGBA',(w,h));im.putdata([tuple(raw8[y*rb+x*4+1:y*rb+x*4+4])+(raw8[y*rb+x*4],) for y in range(h) for x in range(w)]);ip=temp/'input.png';im.save(ip)
            for premultiplied,replace in toggles:
                for keep in (False,True):
                    for thin,thin_type in ((0,2),(-4,1),(4,3)):
                        for blur_type in (1,2,3):
                            for blur in amounts:
                                for depth,fmt in (('PF8','argb8'),('PF16','argb16'),('PF32','argb32f')):
                                    params=[f'Color Keep={int(keep)}',f'Premultiplied Color={int(premultiplied)}','Number of Colors=2','Use Color 1=1','Color 1=255,0,0,0','Use Color 2=1','Color 2=255,0,255,0',f'Amount@14={thin}',f'Distance Type@15={thin_type}',f'Amount@18={blur}',f'Distance Type@19={blur_type}','Direction@20=2',f'Enable Replace={int(replace)}','Use Replace Color 1=1','Replace Color 1=255,224,32,96','Use Replace Color 2=1','Replace Color 2=255,26,89,242']
                                    actual=json.loads(subprocess.check_output([str(args.worker),'render-png',str(aex),str(ip),str(temp/'output.png'),'--pixel-format',fmt,*params],text=True))
                                    if actual['render_error'] or not actual['guards_intact'] or actual['unsupported_suite_calls'] or actual['dropped_unsupported_suite_calls'] or actual['setup']['global_setup_error'] or actual['setup']['params_setup_error']:raise RuntimeError('native exported owner failed')
                                    values={p['slot']:p.get('value') for p in actual['parameter_values']};required={1:int(keep),4:int(premultiplied),14:thin,15:thin_type,18:blur,19:blur_type,20:2,23:int(replace)}
                                    if any(values[k]!=v for k,v in required.items()):raise RuntimeError('parameter propagation drift')
                                    source,_=around.source_fixture(fixture,depth);results={}
                                    for route,name in ((0,'classic'),(1,'smart')):
                                        err,raw=mac_render(exe,fixture,depth,thin,thin_type,keep,route,blur,premultiplied,replace,blur_type)
                                        if not err and len(raw)!=actual['raw_pixel_bytes']:raise RuntimeError('output size drift')
                                        results[name]={'error':err,'sha256':sha(raw) if not err else None,'exact':not err and sha(raw)==actual['raw_pixel_sha256']}
                                    rows.append({'fixture':fixture,'depth':depth,'keep':keep,'premultiplied':premultiplied,'replace':replace,'thin':thin,'type':thin_type,'blur':blur,'blur_type':blur_type,'input_sha256':sha(source),'actual_sha256':actual['raw_pixel_sha256'],'parameter_values':actual['parameter_values'],'guards_intact':actual['guards_intact'],'results':results})
                print(f"{fixture['id']} premultiplied={premultiplied} replace={replace}",flush=True)
    r={'schema':'olmcolorkey.around-range-owner/1','candidate':args.candidate,'case_count':len(rows),'source_sha256':sha(original.encode()),'candidate_source_sha256':sha(body.encode()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.encode()),'worker_sha256':sha(args.worker.read_bytes()),'aex_sha256':sha(aex.read_bytes()),'summary':{name:sum(c['results'][name]['exact'] for c in rows) for name in ('classic','smart')},'cases':rows,'claims_not_made':['No native Windows AE/Mac AE/installed completion','No Windows UCRT fidelity from local math substitutes','No all color-space/threshold/HDR/downsample/ROI completion','No other Blur direction completion']}
    args.report.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(r['summary'])
if __name__=='__main__':main()
