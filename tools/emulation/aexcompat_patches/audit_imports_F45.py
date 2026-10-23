#!/usr/bin/env python3
"""Read the exact campaign AEX import tables, binding them to report hashes."""
import hashlib,json,struct
from pathlib import Path
import pefile
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F45-integrate-ms-double'
rows={}
identities=json.loads((ROOT/'orchestra/reports/F44-evidence/aex-float-imports.json').read_text())
for plugin, identity in sorted(identities.items()):
 p=Path(identity['aex_path'])
 h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==identity['aex_sha256']
 report=S/('before-'+plugin+'-seed1.json')
 if report.exists():
  d=json.loads(report.read_text());assert d['provenance']['aex_sha256']==h
 pe=pefile.PE(str(p));imports={}
 for entry in pe.DIRECTORY_ENTRY_IMPORT:
  names=[i.name.decode() for i in entry.imports if i.name and i.name.decode() in ('sin','cos','exp','pow')]
  if names:imports[entry.dll.decode()]=names
 rows[plugin]={'aex_path':str(p),'aex_sha256':h,'imports':imports}
 print(plugin,imports)
assert len(rows)==10
(ROOT/'orchestra/reports/F45-evidence/aex-double-imports.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
