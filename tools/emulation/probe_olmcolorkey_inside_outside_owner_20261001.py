#!/usr/bin/env python3
"""Compare public Inside/Outside against exported AEX and a temporary recovery."""
import argparse,json,subprocess,tempfile
from pathlib import Path
from PIL import Image
import probe_olmcolorkey_around_range_20261001 as range_owner
around=range_owner.around
thin_owner=range_owner.thin_owner
ROOT=range_owner.ROOT
SOURCE=range_owner.SOURCE
sha=range_owner.sha
HARNESS=range_owner.HARNESS.replace('if(argc!=12)','if(argc!=13)').replace(
    'info.edge_blur_direction=102;', 'info.edge_blur_direction=100+atoi(argv[12]);').replace(
    'FillParams(info,defs,params);', 'FillParams(info,defs,params);\n if(defs[OLMCOLORKEY_EDGE_BLUR_DIRECTION].u.pd.value!=atoi(argv[12]))return 99;')

def candidate_source(body):
    """Static callback reconstruction, never a correction of captured bytes."""
    body=body.replace('IsRecoveredAroundBlur','IsRecoveredPublicBlur')
    old='return info.edge_blur_direction == 102 && info.edge_blur_distance_type >= 1 &&'
    assert body.count(old)==1
    body=body.replace(old,'return info.edge_blur_direction >= 101 && info.edge_blur_direction <= 103 &&\n           info.edge_blur_distance_type >= 1 &&')
    old='const bool use_pf32_positive_thin_outside_caller =\n\t\t    OLMCKPixelTraits<PixelT>::is_32bpc() &&'
    assert body.count(old)==1
    body=body.replace(old,'const bool use_pf32_positive_thin_outside_caller =\n            !IsRecoveredPublicBlur(info) && OLMCKPixelTraits<PixelT>::is_32bpc() &&')
    anchor='\t\t\t\tif (IsRecoveredPublicBlur(info)) {\n\t\t\t\t\t// FUN_180005550'
    assert body.count(anchor)==1
    inside_outside='''				if (IsRecoveredPublicBlur(info) && edge_blur_direction != 2) {
					// FUN_1800053a0/56f0: FLOAT32 distance*pi/amount,
					// double sin and +1, then FLOAT32 conversion and *0.5f.
					// Evaluate the matched matte before the final Keep-off subtraction.
					const float amount = (float)info.edge_blur_amount;
					weight = keep ? 1.0f : 0.0f;
					if (edge_blur_direction == 1) {
						if (keep && native_dist < amount) {
							const float ratio = 3.1415927410125732f / amount;
							const double phase = (double)(native_dist * ratio) - 1.57079632679485;
							weight = (float)(std::sin(phase) + 1.0) * 0.5f;
						}
					} else if (!keep && native_dist < amount) {
						const float ratio = 3.1415927410125732f / amount;
						const double phase = 1.57079632679485 - (double)(native_dist * ratio);
						weight = (float)(std::sin(phase) + 1.0) * 0.5f;
					}
					if (!keep && weight != 0.0f) OLMCKPixelTraits<PixelT>::restore_alpha(*outP, *inP);
					OLMCKPixelTraits<PixelT>::scale_alpha_unbounded(*outP, weight);
					continue;
				}
'''
    return body.replace(anchor,inside_outside+anchor)

def compile_public(directory,body,sanitize=False):
    saved=range_owner.HARNESS
    try:
        range_owner.HARNESS=HARNESS
        return range_owner.compile_public(directory,body,sanitize)
    finally:range_owner.HARNESS=saved

def mac_render(exe,c,route,env=None):
    f=c['fixture'];source,_=around.source_fixture(f,c['depth'])
    run=subprocess.run([str(exe),str(f['width']),str(f['height']),c['depth'][2:],str(c['thin']),str(c['type']),str(int(c['keep'])),str(route),str(c['blur']),str(int(c['premultiplied'])),str(int(c['replace'])),str(c['blur_type']),str(c['direction'])],input=source,check=True,capture_output=True,env=env)
    err=int(run.stderr.decode().strip().split(' ')[1]);assert not err or not run.stdout
    return err,run.stdout

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--candidate',action='store_true');ap.add_argument('--full',action='store_true');ap.add_argument('--boundaries',action='store_true');ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    original=SOURCE.read_text();bodies={'production':original}
    if args.candidate:bodies['candidate']=candidate_source(original)
    rows=[];fixtures=thin_owner.general.FIXTURES if args.full else thin_owner.general.FIXTURES[2:3]
    if args.boundaries:fixtures=({'id':'single_opaque','width':1,'height':1,'alpha':'opaque'},{'id':'column_mixed_zero','width':1,'height':13,'alpha':'mixed'},{'id':'row_mixed_zero','width':9,'height':1,'alpha':'mixed'})
    amounts=(0,1e-50,1e-40,.1,.5,1,1.5,2,4,7.3,31.5,100,4000)
    toggles=((False,False),(False,True),(True,False),(True,True)) if args.full else ((False,False),)
    aex=thin_owner.general.base.retained.actual_probe.AEX
    with tempfile.TemporaryDirectory(prefix='olmck_inside_outside_') as td:
        temp=Path(td);exes={name:compile_public(temp/name,body) for name,body in bodies.items()}
        for fixture in fixtures:
            w,h=fixture['width'],fixture['height'];raw8,rb=around.source_fixture(fixture,'PF8');im=Image.new('RGBA',(w,h));im.putdata([tuple(raw8[y*rb+x*4+1:y*rb+x*4+4])+(raw8[y*rb+x*4],) for y in range(h) for x in range(w)]);ip=temp/'input.png';im.save(ip)
            for premultiplied,replace in toggles:
                for direction in (1,3):
                    for keep in (False,True):
                        for thin,thin_type in ((0,2),(-4,1),(4,3)):
                            for blur_type in (1,2,3):
                                for blur in amounts:
                                    for depth,fmt in (('PF8','argb8'),('PF16','argb16'),('PF32','argb32f')):
                                        params=[f'Color Keep={int(keep)}',f'Premultiplied Color={int(premultiplied)}','Number of Colors=2','Use Color 1=1','Color 1=255,0,0,0','Use Color 2=1','Color 2=255,0,255,0',f'Amount@14={thin}',f'Distance Type@15={thin_type}',f'Amount@18={blur}',f'Distance Type@19={blur_type}',f'Direction@20={direction}',f'Enable Replace={int(replace)}','Use Replace Color 1=1','Replace Color 1=255,224,32,96','Use Replace Color 2=1','Replace Color 2=255,26,89,242']
                                        actual=json.loads(subprocess.check_output([str(args.worker),'render-png',str(aex),str(ip),str(temp/'output.png'),'--pixel-format',fmt,*params],text=True))
                                        if actual['render_error'] or not actual['guards_intact'] or actual['unsupported_suite_calls'] or actual['dropped_unsupported_suite_calls'] or actual['setup']['global_setup_error'] or actual['setup']['params_setup_error']:raise RuntimeError('native exported owner failed')
                                        values={p['slot']:p.get('value') for p in actual['parameter_values']};required={1:int(keep),4:int(premultiplied),14:thin,15:thin_type,18:blur,19:blur_type,20:direction,23:int(replace)}
                                        if any(values[k]!=v for k,v in required.items()):raise RuntimeError('parameter propagation drift')
                                        source,_=around.source_fixture(fixture,depth)
                                        c={'fixture':fixture,'depth':depth,'keep':keep,'premultiplied':premultiplied,'replace':replace,'thin':thin,'type':thin_type,'blur':blur,'blur_type':blur_type,'direction':direction,'input_sha256':sha(source),'actual_sha256':actual['raw_pixel_sha256'],'raw_pixel_bytes':actual['raw_pixel_bytes'],'parameter_values':actual['parameter_values'],'guards_intact':actual['guards_intact'],'results':{}}
                                        for name,exe in exes.items():
                                            c['results'][name]={}
                                            for route,command in ((0,'classic'),(1,'smart')):
                                                err,raw=mac_render(exe,c,route)
                                                if not err and len(raw)!=actual['raw_pixel_bytes']:raise RuntimeError('output size drift')
                                                c['results'][name][command]={'error':err,'sha256':sha(raw) if not err else None,'exact':not err and sha(raw)==actual['raw_pixel_sha256']}
                                        rows.append(c)
                    print(f"{fixture['id']} premultiplied={premultiplied} replace={replace} direction={direction}",flush=True)
    summary={name:{command:sum(c['results'][name][command]['exact'] for c in rows) for command in ('classic','smart')} for name in bodies}
    r={'schema':'olmcolorkey.inside-outside-owner/1','case_count':len(rows),'source_sha256':sha(original.encode()),'candidate_source_sha256':{name:sha(body.encode()) for name,body in bodies.items()},'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.encode()),'worker_sha256':sha(args.worker.read_bytes()),'aex_sha256':sha(aex.read_bytes()),'summary':summary,'cases':rows,'claims_not_made':['No native Windows AE/Mac AE/installed completion','No Windows UCRT fidelity from local math substitutes','No all color-space/threshold/HDR/downsample/ROI completion']}
    # One authored case per line keeps evidence reviewable without dropping fields.
    head=dict(r);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2);text=text[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in rows)+'\n  ]\n}\n'
    args.report.write_text(text);assert json.loads(text)==r;print(summary,flush=True)
if __name__=='__main__':main()
