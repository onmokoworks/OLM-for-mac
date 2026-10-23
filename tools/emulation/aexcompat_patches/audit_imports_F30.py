#!/usr/bin/env python3
"""Read the exact campaign AEX import tables, binding them to report hashes."""
import hashlib,json
from pathlib import Path
import pefile
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F30-oracle-worker-ucrtmath'
rows={}
for report in sorted(S.glob('default-*-seed1.json')):
 d=json.loads(report.read_text());p=Path(d['provenance']['aex_path'])
 h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==d['provenance']['aex_sha256']
 pe=pefile.PE(str(p));imports={}
 for entry in pe.DIRECTORY_ENTRY_IMPORT:
  names=[i.name.decode() for i in entry.imports if i.name and i.name.decode() in ('expf','atan2f','powf')]
  if names:imports[entry.dll.decode()]=names
 rows[d['plugin']]={'aex_path':str(p),'aex_sha256':h,'imports':imports}
 print(d['plugin'],imports)
assert len(rows)==10
Path(__file__).with_name('F30-evidence').joinpath('aex-float-imports.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
