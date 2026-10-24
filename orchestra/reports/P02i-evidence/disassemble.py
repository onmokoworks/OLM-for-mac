"""Read-only confirmation of ColorKey worker allocation and local addressing."""
import json
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
here=Path(__file__).parent
p=json.loads((here/'after-provenance.json').read_text())
pe=pefile.PE(p['aex_path']);base=pe.OPTIONAL_HEADER.ImageBase
md=Cs(CS_ARCH_X86,CS_MODE_64)
with (here/'original-disassembly.txt').open('w') as out:
 out.write('AEX SHA256 '+p['aex_sha256']+'\n')
 for address,size in [(0x1800094b0,480),(0x1800113c0,128),(0x1800117c0,210)]:
  out.write(f'\n0x{address:x}\n')
  for i in md.disasm(pe.get_data(address-base,size),address):
   out.write(f'{i.address:x}: {i.mnemonic} {i.op_str}\n')
