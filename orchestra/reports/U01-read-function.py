"""Stream selected original decomp/asm functions without loading huge listings."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('plugin');p.add_argument('addresses',nargs='+');p.add_argument('--asm',action='store_true')
a=p.parse_args()
root=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
source=root/('disasm' if a.asm else 'decomp')/(a.plugin+('.aex.asm.txt' if a.asm else '.aex.c.txt'))
active=False
for line in source.open():
 if line.startswith('; === ' if a.asm else '// === '):
  active=any((' @ '+s.lower()+' ===') in line.lower() or ('=== '+s+' @') in line for s in a.addresses)
 if active:print(line,end='')
