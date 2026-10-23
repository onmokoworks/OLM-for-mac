#!/usr/bin/env python3
"""Read the exact campaign AEX import tables, binding them to report hashes."""
import hashlib,json,struct
from pathlib import Path
import pefile
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F44-integrate-ms-float'
rows={}
for report in sorted(S.glob('before-*-seed1.json')):
 d=json.loads(report.read_text());p=Path(d['provenance']['aex_path'])
 h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==d['provenance']['aex_sha256']
 pe=pefile.PE(str(p));imports={}
 for entry in pe.DIRECTORY_ENTRY_IMPORT:
  names=[i.name.decode() for i in entry.imports if i.name and i.name.decode() in ('sinf','cosf','log2f')]
  if names:imports[entry.dll.decode()]=names
 rows[d['plugin']]={'aex_path':str(p),'aex_sha256':h,'imports':imports}
 print(d['plugin'],imports)
assert len(rows)==10
(ROOT/'orchestra/reports/F44-evidence/aex-float-imports.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')

p = Path(rows['radialblur']['aex_path'])
pe = pefile.PE(str(p))
boundary = {'aex_sha256': rows['radialblur']['aex_sha256'], 'function': '0x180009a10',
    'constants': {hex(a): {'bits': pe.get_data(a,4).hex(), 'float': struct.unpack('<f',pe.get_data(a,4))[0]}
                  for a in [0x216d4,0x216d0,0x212d4]}}
(ROOT/'orchestra/reports/F44-evidence/radial-log2-boundary.json').write_text(json.dumps(boundary,indent=2)+'\n')
