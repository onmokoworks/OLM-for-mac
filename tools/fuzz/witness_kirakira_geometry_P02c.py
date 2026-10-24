#!/usr/bin/env python3
"""Read-only address-bounded evidence from the original KiraKira AEX."""
import hashlib,json,struct
from pathlib import Path
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'orchestra/state/P02c-kirakira-geometry/static.json'
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 main=main_checkout();aex=main/'plugins_2025/OLMKiraKira.aex';asm=main/'disasm/OLMKiraKira.aex.asm.txt'
 with aex.open('rb') as f:
  f.seek(0x3c);pe=struct.unpack('<I',f.read(4))[0];f.seek(pe+6);count=struct.unpack('<H',f.read(2))[0]
  f.seek(pe+20);optional_size=struct.unpack('<H',f.read(2))[0];f.seek(pe+24+24);base=struct.unpack('<Q',f.read(8))[0]
  rva=0x181486c1c-base;f.seek(pe+24+optional_size);sections=f.read(40*count)
  for i in range(count):
   section=sections[i*40:(i+1)*40];size,va,raw_size,offset=struct.unpack_from('<4I',section,8)
   if va<=rva<va+raw_size:
    f.seek(offset+rva-va);raw=f.read(4);break
  else:raise ValueError('constant outside file sections')
 ranges=[('18114cc88','18114cd6c'),('18114d258','18114d33c'),('18114d828','18114d90c'),('181151710','1811517cc'),('181234f10','181234f92'),('18114ddc0','18114de70'),('18114df3c','18114df58')]
 snippets=[]
 with asm.open() as f:
  for line in f:
   if any(lo<=line[:9]<=hi for lo,hi in ranges):snippets.append(line.rstrip())
 result=dict(aex_sha256=digest(aex),disassembly_sha256=digest(asm),constant=dict(address='0x181486c1c',bytes=raw.hex(),float32=struct.unpack('<f',raw)[0]),snippets=snippets)
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(result['constant'],len(snippets),'instruction lines')
if __name__=='__main__':main()
