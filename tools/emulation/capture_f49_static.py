#!/usr/bin/env python3
"""Hash-bound disassembly supporting F49 arithmetic and selection rules."""
import hashlib,json
from pathlib import Path
import capstone,pefile
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F49-dblur-nonfinite-pf32'
p=ROOT.parent.parent/'plugins_2025/OLMDirectionalBlur.aex'
digest=hashlib.sha256(p.read_bytes()).hexdigest()
assert digest==json.loads((ROOT/'tools/fuzz/declarations/olmdirectionalblur.json').read_text())['aex_sha256']
pe=pefile.PE(str(p));cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
report={'aex_sha256':digest,'ranges':{}}
for name,start,end in [('rotate',0x204e,0x21bd),('scatter',0x1563,0x15d0),('mask',0x6180,0x6198),('writer',0x6bd0,0x6c4a),('normalize',0x62c0,0x6317)]:
 report['ranges'][name]=[dict(address=hex(i.address),bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in cs.disasm(pe.get_data(start,end-start),pe.OPTIONAL_HEADER.ImageBase+start)]
S.mkdir(parents=True,exist_ok=True);(S/'static.json').write_text(json.dumps(report,indent=2)+'\n')
print(digest, {k:len(v) for k,v in report['ranges'].items()})
