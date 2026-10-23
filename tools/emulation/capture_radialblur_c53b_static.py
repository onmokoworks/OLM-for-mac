#!/usr/bin/env python3
"""Retain Radial sampler/prepass/scatter and missing-Layer instruction evidence."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[2]
MAIN=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
SOURCE=MAIN/'disasm/OLMRadialBlur.aex.asm.txt'
OUT=ROOT/'orchestra/reports/C53b-evidence'
RANGES=[(0x9d80,0xa550),(0xb150,0xb630),(0xa9d0,0xb150),(0x5c00,0x5e90),(0x8078,0x8129),(0x1000,0x1270),(0x1cb0,0x2d00),(0x83c0,0x84e0),(0x65c0,0x6810)]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lines=[]
    for line in SOURCE.read_text().splitlines():
        try: address=int(line.split()[0],16)-0x180000000
        except (ValueError,IndexError):continue
        if any(lo<=address<hi for lo,hi in RANGES):lines.append(line.rstrip())
    (OUT/'stages.asm').write_text('\n'.join(lines)+'\n')
    (OUT/'static.json').write_text(json.dumps(dict(source=str(SOURCE),
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),ranges=RANGES,
        extracted_lines=len(lines)),indent=2)+'\n')
    print(len(lines),'instruction lines')
if __name__=='__main__':main()
