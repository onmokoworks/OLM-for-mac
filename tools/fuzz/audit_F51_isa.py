#!/usr/bin/env python3
"""Retain otool evidence and summarize x86_64 instruction requirements."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
from verify_F47d import PLUGINS, ROOT

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundles', type=Path, default=ROOT/'orchestra/state/F51-x86_64-slice-equivalence/bundles')
    p.add_argument('--state', type=Path, default=ROOT/'orchestra/state/F51-x86_64-slice-equivalence/isa')
    args=p.parse_args(); args.state.mkdir(parents=True,exist_ok=True)
    groups={
      'SSE3':set('addsubpd addsubps haddpd haddps hsubpd hsubps lddqu movddup movshdup movsldup'.split()),
      'SSSE3':set('pabsb pabsw pabsd palignr phaddw phaddd phaddsw phsubw phsubd phsubsw pmaddubsw pmulhrsw pshufb psignb psignw psignd'.split()),
      'SSE4.1':set('blendpd blendps blendvpd blendvps dppd dpps extractps insertps movntdqa mpsadbw packusdw pblendvb pblendw pcmpeqq pextrb pextrd pextrq phminposuw pinsrb pinsrd pinsrq pmaxsb pmaxsd pmaxuw pmaxud pminsb pminsd pminuw pminud pmovsxbd pmovsxbq pmovsxbw pmovsxdq pmovsxwd pmovsxwq pmovzxbd pmovzxbq pmovzxbw pmovzxdq pmovzxwd pmovzxwq pmuldq pmulld ptest roundpd roundps roundsd roundss'.split()),
      'SSE4.2':set('crc32b crc32w crc32l crc32q pcmpestri pcmpestrm pcmpgtq pcmpistri pcmpistrm'.split()),
      'other_extensions':set('popcntl popcntq lzcntl lzcntq tzcntl tzcntq andnl andnq bextrl bextrq bzhil bzhiq pdepl pdepq pextl pextq mulxl mulxq rorxl rorxq'.split())}
    records=[]
    for name in PLUGINS.values():
        exe=args.bundles/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name
        dis=args.state/(name+'.disasm')
        with dis.open('w') as f: subprocess.run(['otool','-arch','x86_64','-tvV',str(exe)],stdout=f,check=True)
        counts=collections.Counter(); calls=collections.Counter(); function=''
        examples=[]
        with dis.open() as f:
            for line in f:
                if line.endswith(':\n'): function=line.strip()
                m=re.match(r'^[0-9a-f]{16}\s+(\w+)\s*(.*)',line)
                if not m: continue
                mnemonic,operands=m.groups(); counts[mnemonic]+=1
                if mnemonic.startswith('v') or any(mnemonic in g for g in groups.values()):
                    if len(examples)<40: examples.append(dict(function=function,instruction=line.strip()))
                if 'symbol stub for: _fma' in operands: calls[operands.split('symbol stub for: ')[1]]+=1
        info=subprocess.check_output(['otool','-arch','x86_64','-l',str(exe)],text=True)
        (args.state/(name+'.load-commands')).write_text(info)
        libraries=subprocess.check_output(['otool','-arch','x86_64','-L',str(exe)],text=True)
        records.append(dict(plugin=name,sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
            disassembly_sha256=hashlib.sha256(dis.read_bytes()).hexdigest(), instruction_counts=dict(sorted(counts.items())),
            vex_evex_candidates={k:v for k,v in counts.items() if k.startswith('v')},
            extensions={g:{k:counts[k] for k in sorted(names) if counts[k]} for g,names in groups.items()},
            fma_library_calls=dict(calls),examples=examples,libraries=libraries,
            minos=re.findall(r'(?:minos|version)\s+(11\.0\S*)',info)))
    (args.state/'summary.json').write_text(json.dumps(records,indent=2)+'\n')
    for r in records: print(r['plugin'],r['extensions'],r['vex_evex_candidates'],r['fma_library_calls'])

if __name__=='__main__': main()
