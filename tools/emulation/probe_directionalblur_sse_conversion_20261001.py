#!/usr/bin/env python3
"""Execute the actual AEX scatter CVTTSS2SI instruction at float boundaries."""
import argparse,json,struct
from pathlib import Path
from aex_loader import AexLoader
import probe_directionalblur_general_input_20261001 as owner
from unicorn.x86_const import UC_X86_REG_XMM0,UC_X86_REG_R9D
BITS=(0,0x80000000,0x3f800000,0xbf800000,0x3fc00000,0xbfc00000,0x00000001,0x80000001,0x4effffff,0x4f000000,0x4f000001,0xceffffff,0xcf000000,0xcf000001,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00000,0xffc00000)
ADDRESS=0x180001450
EXPECTED_INSTRUCTION=bytes.fromhex('f3440f2cc8')
def expected(bits):
    value=struct.unpack('<f',struct.pack('<I',bits))[0]
    return -2147483648 if not (-2147483648.0<=value<2147483648.0) else int(value)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    loader=AexLoader(str(owner.AEX),verbose=False,fast=False)
    instruction=loader.read_bytes(ADDRESS,5)
    if instruction!=EXPECTED_INSTRUCTION:raise RuntimeError('scatter conversion instruction changed')
    cases=[]
    for bits in BITS:
        loader.uc.reg_write(UC_X86_REG_XMM0,bits);loader.uc.reg_write(UC_X86_REG_R9D,0x12345678)
        loader.uc.emu_start(ADDRESS,ADDRESS+5,count=1)
        result=loader.uc.reg_read(UC_X86_REG_R9D);signed=struct.unpack('<i',struct.pack('<I',result))[0]
        cases.append({'input_f32_bits':f'{bits:08x}','native_i32':signed,'expected_i32':expected(bits),'exact':signed==expected(bits)})
    report={'schema':'directionalblur.scatter-sse-conversion/1','aex_sha256':owner.sha(owner.AEX.read_bytes()),'probe_sha256':owner.sha(Path(__file__).read_bytes()),'address':f'{ADDRESS:x}','instruction_hex':instruction.hex(),'instruction':'CVTTSS2SI R9D,XMM0','case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'cases':cases,'claims_not_made':['Local instruction emulation is not native AE/UCRT verification','No whole render or arbitrary input completion']}
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('EXACT',report['exact_count'],'/',len(cases))
if __name__=='__main__':main()
