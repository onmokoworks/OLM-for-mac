#!/usr/bin/env python3
"""Disassemble the hash-pinned ORIGINAL AEX, without a Ghidra database dependency."""
import argparse,hashlib,json,sys
sys.dont_write_bytecode=True
from pathlib import Path
import capstone,pefile
ROOT=Path(__file__).resolve().parents[2]
MAIN=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
RANGES=[(0x40f0,0x4260),(0x43c0,0x4460),(0x45a0,0x4640),(0x4640,0x6510),
        (0x65c0,0x8540),(0x8690,0x8930),(0x9360,0x9380),(0xd9d0,0xdaa0),(0x19f20,0x19f80)]
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    src=MAIN/'aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex'
    digest=hashlib.sha256(src.read_bytes()).hexdigest()
    assert digest=='ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb'
    pe=pefile.PE(str(src));md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
    lines=[]
    for lo,hi in RANGES:
        lines.append(f'\n# RVA {lo:x}..{hi:x}')
        for i in md.disasm(pe.get_data(lo,hi-lo),lo):lines.append(f'{i.address:08x} {i.bytes.hex():32} {i.mnemonic} {i.op_str}')
    body='\n'.join(lines)+'\n';(a.output/'original.asm').write_text(body)
    (a.output/'static.json').write_text(json.dumps(dict(aex_sha256=digest,ranges=RANGES,capstone_version=capstone.__version__,asm_sha256=hashlib.sha256(body.encode()).hexdigest(),lines=len(lines)),indent=2)+'\n')
    print(len(lines),'lines')
if __name__=='__main__':main()
