#!/usr/bin/env python3
"""Recheck original resources/setup; bind current source and cached bundle metadata."""
import json,sys,os,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'))
from audit_route_flags_F18 import pe_pipls,mac_pipls,original_setup,sha
import pefile
MAIN=Path('/Users/onmk/Documents/Projects/Personal/OLM as');S=ROOT/'orchestra/state/T14-classic-route-triage';os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
old=json.loads((ROOT/'reports/route_flags_F18_after.json').read_text());rows=[]
B=Path.home()/'.cache/olm-emu/I03-bundles-545f06bd924497e5/bundles/xcode'
for p in old['plugins']:
 path=Path(p['aex_path']);pe=pefile.PE(str(path));pipl=pe_pipls(pe)
 setup=original_setup(path,int(p['entry'],16),0)
 bundle=B/p['plugin']/'products'/(p['plugin']+'.plugin')/'Contents'
 resources=list((bundle/'Resources').glob('*.rsrc'))
 mp=mac_pipls(resources[0]);exports=[s.name.decode() for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name]
 assert sha(path)==p['aex_sha256']
 assert [setup[k] for k in ('out_flags','out_flags2')]==[pipl[0][k] for k in ('out_flags','out_flags2')]==[mp[0][k] for k in ('out_flags','out_flags2')]
 row={'plugin':p['plugin'],'aex_sha256':sha(path),'exports':exports,'original_pipl':pipl,'original_setup':setup,'cached_mac_pipl':mp,'bundle_sha256':sha(bundle/'MacOS'/p['plugin'])}
 rows.append(row);print(p['plugin'],hex(setup['out_flags']),hex(setup['out_flags2']),exports,flush=True)
(S/'metadata.json').write_text(json.dumps(rows,indent=2)+'\n')
# Keep only bounded static excerpts, binding each original source by a streaming hash.
import hashlib
excerpts=[('OLMColorKey.aex.c.txt',[(5959,5967),(8981,9008),(9084,9090),(9447,9493)]),('OLMDirectionalBlur.aex.c.txt',[(4028,4065),(4103,4111),(4148,4180)]),('DistanceGradation.aex.c.txt',[(3540207,3540274),(3540276,3540360),(3540450,3540536),(3542680,3542742)])]
for name,ranges in excerpts:
 h=hashlib.sha256();picked=[]
 with (MAIN/'decomp'/name).open('rb') as f:
  for n,line in enumerate(f,1):
   h.update(line)
   if any(a<=n<=b for a,b in ranges):picked.append(f'{n}: '+line.decode(errors='replace'))
 (S/(name+'.excerpt')).write_text('source: '+str(MAIN/'decomp'/name)+'\nsha256: '+h.hexdigest()+'\n'+''.join(picked))
