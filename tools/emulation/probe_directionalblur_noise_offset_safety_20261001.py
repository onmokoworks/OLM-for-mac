#!/usr/bin/env python3
"""Retain candidate negative-offset safety failures without changing native math."""
import argparse,json,os,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_general_features_20261001 as feature
import probe_directionalblur_fixed_getter_20261001 as fixed
from aex_loader import AexLoader
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
sha=feature.sha
ROOT=feature.owner.ROOT
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    rows=[]
    with tempfile.TemporaryDirectory(prefix='dblur_negative_') as td:
        binary=Path(td)/'sanitized';previous=fixed.HARNESS
        try:fixed.HARNESS=feature.HARNESS;fixed.compile_harness(binary,True)
        finally:fixed.HARNESS=previous
        env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
        for offset in (-32768,-720,-36,-35,-18,32767):
            for depth in (16,32):
                params={5:7,10:11,15:73.75,19:offset};data=feature.owner.typed(feature.owner.pixels(9,7,True),depth)
                q=subprocess.run([str(binary),'9','7',str(depth),','.join(f'{s}={v}' for s,v in params.items())],input=data,capture_output=True,env=env)
                err=q.stderr.decode();kind='UBSan unsigned pointer offset overflow' if 'addition of unsigned offset' in err and 'overflowed' in err else 'ASan heap-buffer-overflow' if 'AddressSanitizer: heap-buffer-overflow' in err else 'none' if q.returncode==0 else 'other_failure'
                rows.append({'offset':offset,'depth':depth,'parameters':params,'geometry':[9,7],'input_sha256':sha(data),'exit_code':q.returncode,'sanitizer_result':kind,'public_admission':'rejected; candidate only'})
    # This excerpt is the actual AEX: only the upper bound is folded before
    # signed truncation and the indexed table reads. No lower-bound fold exists.
    loader=AexLoader(str(feature.owner.AEX),verbose=False,fast=False)
    start=0x1800037a4;raw=loader.read_bytes(start,0x37fe-0x37a4)
    instructions=[{'rva':hex(i.address-0x180000000),'mnemonic':i.mnemonic,'operands':i.op_str} for i in Cs(CS_ARCH_X86,CS_MODE_64).disasm(raw,start)]
    assert [i['mnemonic'] for i in instructions][:9]==['xorps','cvtsi2ss','comiss','jb','subss','comiss','jae','cvttss2si','xorps']
    r={'schema':'directionalblur.noise-offset-safety/1','production_source_sha256':sha(feature.owner.SOURCE.read_bytes()),'core_noise_sha256':sha((ROOT/'core/dblur_noise.h').read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(feature.HARNESS.read_bytes()),'aex_sha256':sha(feature.owner.AEX.read_bytes()),'loader_sha256':sha((ROOT/'tools/emulation/aex_loader.py').read_bytes()),'native_generator_rva':'0x34e0','native_table_index_instructions':instructions,'native_instruction_bytes_sha256':sha(raw),'cases':rows,'case_count':len(rows),'sanitizer_failure_count':sum(x['exit_code']!=0 for x in rows),'native_static_fact':'Upper-bound subtraction only; signed negative index reaches table read','inference':'Negative Offset below -36 can read before the native allocated noise table; host behavior needs allocation-bound witness','claims_not_made':['No native memory-bound execution proof yet','No numeric comparison for invalid candidate memory access','No public admission change','No full compatibility completion']}
    assert r['sanitizer_failure_count']==4 and all(x['sanitizer_result']!='other_failure' for x in rows)
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('RETAINED SAFETY FAILURE',r['sanitizer_failure_count'],'/',len(rows))
if __name__=='__main__':main()
