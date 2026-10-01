#!/usr/bin/env python3
"""Locate subnormal Blur differences at native SSE NaN and integer conversion."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
import colorkey_public_blur_candidate_20261001 as recovery
owner=recovery.initial

def native_render(worker,temp,c):
    f=c['fixture'];data,rb=owner.around.source_fixture(f,c['depth']);ps={'PF8':4,'PF16':8,'PF32':16}[c['depth']]
    packed=b''.join(data[y*rb:y*rb+f['width']*ps] for y in range(f['height']))
    payload='v4|'+';'.join(f"param_{v['slot']}@{v['slot']}:argb8="+','.join(map(str,v['color'])) if 'color' in v else f"param_{v['slot']}@{v['slot']}:f64={v['value']}" for v in c['parameter_values'])
    req={'v':4,'type':'render_frame','frame_index':0,'current_time':{'value':0,'scale':24,'step':1,'total':1},'parameters':payload};message=json.dumps(req).encode()
    ip=temp/'input.raw';op=temp/'output.raw';ip.write_bytes(packed)
    run=subprocess.run([str(worker),'session',str(owner.thin_owner.general.base.retained.actual_probe.AEX),str(ip),str(op),str(f['width']),str(f['height']),'24','--pixel-format',{'PF8':'argb8','PF16':'argb16','PF32':'argb32f'}[c['depth']]],input=struct.pack('<I',len(message))+message,capture_output=True,check=True)
    messages=[];pos=0
    while pos<len(run.stdout):
        n=struct.unpack_from('<I',run.stdout,pos)[0];pos+=4;messages.append(json.loads(run.stdout[pos:pos+n]));pos+=n
    frame=next(m for m in messages if m['type']=='frame_done');raw=op.read_bytes()
    assert frame['status']=='ok' and frame['render_error']==0 and frame['output']['guards_intact'] and frame['output']['render_path']=='smartfx' and frame['output']['checksum']==owner.sha(raw)
    assert owner.sha(raw)==c['actual_sha256']
    return raw,frame,payload

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    native_report=owner.ROOT/'reports/colorkey_inside_outside_baseline_candidate_20261001.json';r=json.loads(native_report.read_text());cases=[c for c in r['cases'] if not c['results']['candidate']['classic']['exact']]
    assert len(cases)==12 and all(c['depth']=='PF32' and c['direction']==1 and c['blur']==1e-40 for c in cases)
    original=owner.SOURCE.read_text();first=owner.candidate_source(original);revised=recovery.candidate_source(original);rows=[]
    with tempfile.TemporaryDirectory(prefix='olmck_nan_semantics_') as td:
        temp=Path(td);exes={'first':owner.compile_public(temp/'first',first),'revised':owner.compile_public(temp/'revised',revised)}
        for c in cases:
            raw,frame,payload=native_render(args.worker,temp,c);results={};diff=[]
            for name,exe in exes.items():
                err,mac=owner.mac_render(exe,c,0);assert not err
                results[name]={'sha256':owner.sha(mac),'exact':mac==raw}
                if name=='first':
                    for i in range(0,len(raw),16):
                        if raw[i:i+4]!=mac[i:i+4]:diff.append({'pixel':i//16,'native_alpha_bits':raw[i:i+4].hex(),'first_alpha_bits':mac[i:i+4].hex()})
            assert diff and all(d['native_alpha_bits']=='0000c0ff' and d['first_alpha_bits']=='0000c07f' for d in diff)
            assert results['revised']['exact']
            rows.append({'condition':{k:c[k] for k in ('fixture','depth','keep','thin','type','blur','blur_type','direction')},'parameter_payload':payload,'input_sha256':c['input_sha256'],'native_sha256':owner.sha(raw),'frame_done':frame,'results':results,'different_alpha_count':len(diff),'first_differences':diff[:8]})
    out={'schema':'olmcolorkey.blur-nan-semantics/1','case_count':len(rows),'source_sha256':owner.sha(original.encode()),'first_candidate_source_sha256':owner.sha(first.encode()),'revised_candidate_source_sha256':owner.sha(revised.encode()),'probe_sha256':owner.sha(Path(__file__).read_bytes()),'candidate_tool_sha256':owner.sha(Path(recovery.__file__).read_bytes()),'native_case_report_sha256':owner.sha(native_report.read_bytes()),'worker_sha256':owner.sha(args.worker.read_bytes()),'aex_sha256':r['aex_sha256'],'static_instruction_facts':[{'address':'0x1800054a2','instruction':'mulss xmm0,xmm9'},{'address':'0x1800054a7','instruction':'cvtps2pd xmm0,xmm0'},{'address':'0x1800054aa','instruction':'subsd xmm0,xmm10'},{'address':'0x1800084a4','instruction':'cvttss2si ecx,xmm0'},{'address':'0x1800084a8','instruction':'mov word ptr [rax],cx'},{'address':'0x180008733','instruction':'cvttss2si ecx,xmm0'},{'address':'0x180008737','instruction':'mov byte ptr [rax],cl'}],'binary_constants':[{'rva':'0x1f688','value':.5,'bits':'0000003f'},{'rva':'0x1f6d0','value':1.57079632679485,'bits':'462c4454fb21f93f'},{'rva':'0x1f6e0','value':3.1415927410125732,'bits':'db0f4940'}],'cases':rows,'claims_not_made':['No native Windows UCRT/AE proof','No normal AE UI generation of subnormal Blur proved','NaN sign is recovered at invalid phase multiplication, not corrected in final output']}
    args.report.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print('NAN_SEMANTICS',len(rows),'exact')
if __name__=='__main__':main()
