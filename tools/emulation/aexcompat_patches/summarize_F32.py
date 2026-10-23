#!/usr/bin/env python3
"""Bind compact review evidence to fresh F32 validation reports."""
import collections,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
S=ROOT/'orchestra/state/F32-smoother-oracle-deep-pixels'
E=HERE/'F32-evidence'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 E.mkdir(exist_ok=True)
 def read(n):return json.loads((S/n).read_text())
 campaigns=[read(n) for n in ('f30-seed1.json','f32-seed1.json','fixed-seed1.json')]
 rows=[]
 for a,b,c in zip(*(d['cases'] for d in campaigns)):
  assert a['input_sha256']==b['input_sha256']==c['input_sha256']
  assert a['index']==b['index']==c['index']
  assert b['result']['oracle']==c['result']['oracle']
  for route in ('classic','smart'):
   if a['result']['routes'][route]['status']=='exact':assert c['result']['routes'][route]['status']=='exact'
   if b['result']['routes'][route]['status']=='exact':assert c['result']['routes'][route]['status']=='exact'
  rows.append(dict(index=a['index'],depth=a['depth'],input_sha256=a['input_sha256'],before=a['result'],deep_only=b['result'],fixed=c['result']))
 assert len(rows)==300
 hosts=read('host-import-differential.json')
 short=[]
 for r in hosts['rows']:
  a,b=r['unimplemented'],r['implemented']
  first=next((dict(index=i,before=x,after=y) for i,(x,y) in enumerate(zip(a['imports'],b['imports'])) if x['output']!=y['output']),None)
  assert first and first['before']['input']==first['after']['input']
  short.append(dict(corpus=r['corpus'],worker_sha256=r['worker_sha256'],unimplemented_sha256=a['sha256'],implemented_sha256=b['sha256'],fixed_equal=r['fixed_equal'],first_import_difference=first,import_counts=[len(a['imports']),len(b['imports'])],scan_counts=[len(a['scans']),len(b['scans'])],scan_differences=[dict(index=i,before=x,after=y) for i,(x,y) in enumerate(zip(a['scans'],b['scans'])) if x!=y]))
 summary=dict(campaigns=[dict(summary=d['summary'],provenance=d['provenance']) for d in campaigns],lost_exact=0,rows=rows,hosts=dict(frozen_boundary=hosts['frozen_boundary'],total=hosts['total'],fixed_equal=hosts['fixed_equal'],unimplemented_equal=hosts['unimplemented_equal'],rows=short),raw_report_sha256={n:sha(S/n) for n in ('f30-seed1.json','f32-seed1.json','fixed-seed1.json','host-import-differential.json')})
 (E/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 for n in ('build-manifest.json','corpus-differential.json','classifier.json','sanitized.json','deep-callbacks.json'):
  shutil.copy2(S/n,E/n)
 print('300 campaign rows, zero lost exact; hosts',hosts['fixed_equal'],'/',hosts['total'])
if __name__=='__main__':main()
