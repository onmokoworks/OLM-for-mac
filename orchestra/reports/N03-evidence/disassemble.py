import sys
sys.path.insert(0,'tools/emulation')
from aex_loader import AexLoader
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
ld=AexLoader('/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/DistanceGradation.aex',verbose=False,fast=True)
cs=Cs(CS_ARCH_X86,CS_MODE_64)
for lo,hi in [(0x1806b7240,0x1806b7d40),(0x1806bd9a0,0x1806be1e0)]:
 for i in cs.disasm(ld.read_bytes(lo,hi-lo),lo):print(f'{i.address:x}: {i.mnemonic} {i.op_str}'.rstrip())
