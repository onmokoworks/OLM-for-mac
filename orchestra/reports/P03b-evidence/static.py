"""Decode unchanged original instructions relevant to the PF32 admission paths."""
import hashlib
from pathlib import Path
import capstone, pefile
main = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
import sys
name = sys.argv[1] if len(sys.argv)>1 else 'OLMDirectionalBlur'
p = main/'plugins_2025'/f'{name}.aex'
data = p.read_bytes(); pe = pefile.PE(data=data)
print('AEX SHA256', hashlib.sha256(data).hexdigest())
image = pe.get_memory_mapped_image()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
regions = [(0x1ec0,0x2250),(0x6b30,0x6c50),(0x1000,0x1830)] if name == 'OLMDirectionalBlur' else [(0x11749a0,0x1174da0),(0x1170c90,0x1170ff0),(0x117c580,0x117c680)]
if name == 'OLMRadialBlur': regions = [(0x8162,0x81f0),(0x9d80,0x9e70)]
if name == 'OLMKiraKira': regions = [(0x114ec60,0x114ee00),(0x11501b0,0x1150270),(0x1156740,0x1156780),(0x114ffd0,0x11501b0)]
for start,end in regions:
    print('\nRVA',hex(start),hex(end))
    for ins in md.disasm(image[start:end],pe.OPTIONAL_HEADER.ImageBase+start):
        print(f'{ins.address:x} {ins.mnemonic:10} {ins.op_str}'.rstrip())
