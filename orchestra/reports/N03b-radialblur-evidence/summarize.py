"""Retain all observed snapshots and summarize the corrupt-descriptor boundary."""
import gzip, hashlib, json, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/N03b-radialblur-v2-mismatch'
OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[]
for d in sorted((S/'trace').iterdir()):
 t=json.loads((d/'trace.json').read_text());ws={w['watch_id']:w for w in t['memory_witnesses']}
 assert not t['truncated'] and not t['dropped_memory_witnesses'] and not t['trace_configuration']['unhookable_watches']
 r=json.loads((d/'result.json').read_text());assert r['bound']
 dest=ws['copy-dest'];before=bytes.fromhex(dest['before']['hex']);after=bytes.fromhex(dest['after']['hex'])
 assert dest['before']['address']==0x1000000001 and after==bytes(120)
 owner=ws['6d10-input' if d.name.startswith('ab') else '7d30-input']
 assert owner['before']['address']==0x1000000000 and bytes.fromhex(owner['before']['hex'])==bytes(128)
 builder=bytes.fromhex(ws['builder-context']['before']['hex'])
 assert struct.unpack_from('<Q',builder,0xa8)[0]==0x1000000001
 comparisons={}
 for label,macname,when in [('source','source','before'),('polar','polar','before'),('scalar','scalar','before'),('normalized','normalized','after')]:
  if label not in ws:continue
  a=bytes.fromhex(ws[label][when]['hex']);b=(S/'mac'/d.name/(macname+'.bin')).read_bytes()
  assert len(a)==len(b)
  diffs=[i for i in range(0,len(a),4) if a[i:i+4]!=b[i:i+4]]
  i=diffs[0] if diffs else None
  comparisons[label]=dict(bytes=len(a),different_words=len(diffs),first_word=None if i is None else i//4,original=None if i is None else a[i:i+4].hex(),mac=None if i is None else b[i:i+4].hex(),original_sha256=sha(a),mac_sha256=sha(b))
 rows.append(dict(witness=d.name,execution=r,witnesses=len(ws),copy_destination=hex(dest['before']['address']),input_world=hex(owner['before']['address']),descriptor_before=dict(data=hex(struct.unpack_from('<Q',before,23)[0]),rowbytes=struct.unpack_from('<i',before,31)[0],width=struct.unpack_from('<i',before,35)[0],height=struct.unpack_from('<i',before,39)[0]),descriptor_after_zero=True,comparisons=comparisons,missing_watch_ids=sorted(set(x['id'] for x in json.loads((d/'watches.json').read_text()))-set(ws))))
 # The compressed trace includes every complete before/after snapshot. Validate raw files too.
 for j,w in enumerate(t['memory_witnesses']):
  for when in ('before','after'):
   if w[when]['status']=='captured':assert (d/f'trace.json.{j:03}.{when}.bin').read_bytes()==bytes.fromhex(w[when]['hex'])
 destdir=OUT/'captures'/d.name;destdir.mkdir(parents=True,exist_ok=True)
 for name in ('trace.json','watches.json','result.json'):
  (destdir/(name+'.gz')).write_bytes(gzip.compress((d/name).read_bytes(),mtime=0))
 for p in (S/'mac'/d.name).glob('*.bin'):
  (destdir/('mac-'+p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
(OUT/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
for name in ('original.asm','static.json'):
 (OUT/(name+'.gz')).write_bytes(gzip.compress((S/'static'/name).read_bytes(),mtime=0))
manifest=[dict(path=str(p.relative_to(OUT)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json']
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for r in rows:print(r['witness'],r['descriptor_before'],r['comparisons'], 'missing',r['missing_watch_ids'])
