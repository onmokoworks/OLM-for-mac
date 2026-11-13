"""Read-only, hash-bound disassembly witness for the original no-op PF_COPY route.
Requires pefile and capstone. Pair with `directional-noop-abi` for SDK offsets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pefile
import capstone

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--original',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
pe=pefile.PE(str(a.original)); image=pe.get_memory_mapped_image(); base=pe.OPTIONAL_HEADER.ImageBase
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
text=next(s for s in pe.sections if s.Name.startswith(b'.text'))
instructions=list(md.disasm(image[text.VirtualAddress:text.VirtualAddress+text.Misc_VirtualSize],base+text.VirtualAddress))
regions={}
for name,start,length in [('smart8_copy_and_zero_gate',0x4a20,0x149),('smart16_copy_and_zero_gate',0x3c90,0x149),('smart32_copy_and_zero_gate',0x57b0,0x160),('depth_dispatch',0x7c90,0x1d1)]:
 regions[name]=[{'address':hex(i.address),'bytes':i.bytes.hex(),'instruction':i.mnemonic+' '+i.op_str} for i in instructions if base+start<=i.address<base+start+length]
assert hashlib.sha256(a.original.read_bytes()).hexdigest() == 'd3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e', 'different original: rebind addresses'
assert any(i['address']=='0x180004abb' and i['instruction']=='call qword ptr [rax + 0x40]' for i in regions['smart8_copy_and_zero_gate'])
report={'artifact':str(a.original.resolve()),'sha256':hashlib.sha256(a.original.read_bytes()).hexdigest(),'image_base':hex(base),'regions':regions,
 'observation':'Smart8 loads [in_data+0xb0], passes effect_ref [in_data+0xb8], source/destination and two null rectangles, calls [utils+0x40], then tests four scaled/truncated lengths and exits when all are zero.',
 'abi_binding':'directional-noop-abi asserts PF_InData.utils=0xb0, effect_ref=0xb8, PF_UtilCallbacks.copy=0x40 on Windows x64.',
 'limit':'Static call/branch evidence, not native AE runtime observation. The implementation of PF_COPY belongs to the host, not this AEX.'}
a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
