#!/usr/bin/env python3
"""Witness the native float Blur amount boundary before public parameter edits."""
import argparse,json,subprocess,tempfile
from pathlib import Path
from PIL import Image
import probe_olmcolorkey_around_range_20261001 as around

def normalized_source(body):
    for old,new in (
        ('info->edge_blur_amount = params[OLMCOLORKEY_EDGE_BLUR_AMOUNT]->u.fs_d.value;', 'info->edge_blur_amount = static_cast<float>(params[OLMCOLORKEY_EDGE_BLUR_AMOUNT]->u.fs_d.value);'),
        ('info->edge_blur_amount = p.u.fs_d.value;', 'info->edge_blur_amount = static_cast<float>(p.u.fs_d.value);')):
        assert body.count(old)==1;body=body.replace(old,new)
    return body

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--production',action='store_true');ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();original=around.SOURCE.read_text();rows=[]
    fixture=around.thin_owner.general.FIXTURES[2];w,h=fixture['width'],fixture['height'];aex=around.thin_owner.general.base.retained.actual_probe.AEX
    body=original if args.production else around.candidate_source(original)
    bodies={'production':body} if args.production else {'range_candidate':body,'float_candidate':normalized_source(body)}
    with tempfile.TemporaryDirectory(prefix='olmck_float_amount_') as td:
        temp=Path(td);executables={name:around.compile_public(temp/name,b) for name,b in bodies.items()}
        raw,rb=around.around.source_fixture(fixture,'PF8');im=Image.new('RGBA',(w,h));im.putdata([tuple(raw[y*rb+x*4+1:y*rb+x*4+4])+(raw[y*rb+x*4],) for y in range(h) for x in range(w)]);ip=temp/'input.png';im.save(ip)
        for amount in (0,1e-50,1e-40,.1,1.5):
            for keep in (False,True):
                for depth,fmt in (('PF8','argb8'),('PF16','argb16'),('PF32','argb32f')):
                    params=[f'Color Keep={int(keep)}','Premultiplied Color=0','Number of Colors=2','Use Color 1=1','Color 1=255,0,0,0','Use Color 2=1','Color 2=255,0,255,0','Amount@14=0','Distance Type@15=2',f'Amount@18={amount}','Distance Type@19=2','Direction@20=2','Enable Replace=0','Use Replace Color 1=1','Replace Color 1=255,224,32,96','Use Replace Color 2=1','Replace Color 2=255,26,89,242']
                    actual=json.loads(subprocess.check_output([str(args.worker),'render-png',str(aex),str(ip),str(temp/'output.png'),'--pixel-format',fmt,*params],text=True))
                    assert not actual['render_error'] and actual['guards_intact'] and not actual['unsupported_suite_calls'] and not actual['dropped_unsupported_suite_calls']
                    values={p['slot']:p.get('value') for p in actual['parameter_values']};assert values[18]==amount and values[20]==2
                    source,_=around.around.source_fixture(fixture,depth);results={}
                    for name,exe in executables.items():
                        results[name]={}
                        for route,label in ((0,'classic'),(1,'smart')):
                            err,raw=around.mac_render(exe,fixture,depth,0,2,keep,route,amount,False,False,2)
                            results[name][label]={'error':err,'sha256':around.sha(raw) if not err else None,'exact':not err and around.sha(raw)==actual['raw_pixel_sha256']}
                    rows.append({'fixture':fixture,'depth':depth,'keep':keep,'amount':amount,'input_sha256':around.sha(source),'actual_sha256':actual['raw_pixel_sha256'],'parameter_values':actual['parameter_values'],'guards_intact':actual['guards_intact'],'results':results})
    r={'schema':'olmcolorkey.blur-float-materialization/1','production':args.production,'case_count':len(rows),'source_sha256':around.sha(original.encode()),'candidate_source_sha256':{k:around.sha(v.encode()) for k,v in bodies.items()},'probe_sha256':around.sha(Path(__file__).read_bytes()),'worker_sha256':around.sha(args.worker.read_bytes()),'aex_sha256':around.sha(aex.read_bytes()),'summary':{name:{route:sum(c['results'][name][route]['exact'] for c in rows) for route in ('classic','smart')} for name in bodies},'cases':rows,'claims_not_made':['Tiny positive double sliders are not proof of ordinary UI generation','No native AE/UCRT/installed proof']}
    args.report.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(r['summary'])
if __name__=='__main__':main()
