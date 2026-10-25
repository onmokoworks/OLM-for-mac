"""Run with MAIN tools/emulation/.venv/bin/python (capstone and pefile)."""
from pathlib import Path
import hashlib, capstone, pefile
p=Path('/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/OLMColorKey.aex')
data=p.read_bytes(); pe=pefile.PE(data=data); image=pe.get_memory_mapped_image()
print('AEX SHA256',hashlib.sha256(data).hexdigest())
for start,end in ((0x43a0,0x4850),(0x9960,0x9e10)):
 for i in capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64).disasm(image[start:end],0x180000000+start):
  print(hex(i.address),i.mnemonic,i.op_str)
