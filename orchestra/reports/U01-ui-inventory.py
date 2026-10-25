"""Read-only PE inventory. Run with MAIN's emulation venv (pefile)."""
import hashlib,json,struct
from pathlib import Path
import pefile
ROOT=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
rows=[]
for p in sorted((ROOT/'plugins_2025').glob('*.aex')):
 pe=pefile.PE(str(p)); base=pe.OPTIONAL_HEADER.ImageBase
 row=dict(plugin=p.stem,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pipl=[],gdi_imports=[])
 for dll in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[]):
  if dll.dll.lower() in [b'gdi32.dll',b'user32.dll']:
   row['gdi_imports'] += [dll.dll.decode()+':'+(i.name or b'ordinal').decode() for i in dll.imports]
 for typ in pe.DIRECTORY_ENTRY_RESOURCE.entries:
  if str(typ.name).upper()!='PIPL': continue
  for name in typ.directory.entries:
   for lang in name.directory.entries:
    d=lang.data.struct; data=pe.get_data(d.OffsetToData,d.Size)
    props={}
    for key in (b'OLGe',b'2LGe'):
     pos=data.index(b'MIB8'+key)
     assert struct.unpack_from('<I',data,pos+12)[0]==4
     props[key[::-1].decode()]=hex(struct.unpack_from('<I',data,pos+16)[0])
    row['pipl'].append(dict(resource=name.id,flags=props,hex=data.hex()))
 # Resolve the active C++ effect table referenced by the exported entry constructor.
 textsec=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
 lo=base+textsec.VirtualAddress; hi=lo+textsec.Misc_VirtualSize
 entry=False; tables=[]
 import re
 for line in (ROOT/'disasm'/(p.stem+'.aex.asm.txt')).open():
  if line.startswith('; === '): entry='entry_point @' in line
  if entry and 'LEA' in line:
   m=re.search(r'\[0x([0-9a-f]+)\]',line)
   if m:
    va=int(m[1],16)
    try: ptrs=struct.unpack('<13Q',pe.get_data(va-base,104))
    except Exception: continue
    if all(lo<=v<hi for v in ptrs):tables.append([hex(va),*[hex(v) for v in ptrs]])
 row['effect_vtables']=tables
 rows.append(row)
print(json.dumps(rows,indent=2))
