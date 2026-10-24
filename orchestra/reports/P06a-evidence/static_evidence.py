"""Read-only disassembly and decompilation excerpts for the P06a boundary."""
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
R=Path(__file__).resolve().parents[3];M=R.parent.parent;E=Path(__file__).parent
p=pefile.PE(str(M/'plugins_2025/OLMDirectionalBlur.aex'));cs=Cs(CS_ARCH_X86,CS_MODE_64)
lines=[]
for a,n in [(0x1000,280),(0x122f,45),(0x61d0,110)]:
 for x in cs.disasm(p.get_data(a,n),0x180000000+a):lines.append(f'{hex(x.address)} {x.mnemonic} {x.op_str}')
(E/'disassembly.txt').write_text('\n'.join(lines)+'\n')
text=(M/'decomp/OLMDirectionalBlur.aex.c.txt').read_text()
parts=[]
for name in ('FUN_180001830','FUN_180007bd0'):
 a=text.index('// === '+name);b=text.index('// === ',a+8);parts.append(text[a:b])
(E/'storage-excerpts.txt').write_text('\n'.join(parts))
