"""Summarize and archive N03 output-bound diagnostics without dumping raw JSON."""
import gzip, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=ROOT/'orchestra/state/N03-radialblur-v2-mismatch'
out=Path(__file__).resolve().parent
rows=[]
for p in sorted((s/'watch-b150-1048576-first').glob('*/trace.json')):
 name=p.parent.name
 trace=json.loads(p.read_text())
 witness=next(m for m in trace['memory_witnesses'] if m['watch_id']=='output')
 left=bytes.fromhex(witness['before']['hex'])
 right=(s/'mac'/name/'polar.bin').read_bytes()
 size=min(len(left),len(right))
 differing=[i for i in range(0,size,4) if left[i:i+4]!=right[i:i+4]]
 row=dict(name=name,stage='polar before B150',captured_bytes=len(left),mac_plane_bytes=len(right),compared_bytes=size,complete_plane=len(left)>=len(right),differing_words=len(differing),first=None if not differing else dict(word=differing[0]//4,original=left[differing[0]:differing[0]+4].hex(),mac=right[differing[0]:differing[0]+4].hex()),original_compared_all_zero=not any(left[:size]),original_output_binding=json.loads(p.with_name('result.json').read_text()),mac=json.loads((s/'mac/report.json').read_text())[name])
 rows.append(row)
summary=dict(cases=rows,watches=[])
for p in sorted(s.glob('watch-*/*/trace.json')):
 trace=json.loads(p.read_text());result=json.loads(p.with_name('result.json').read_text())
 summary['watches'].append(dict(watch=p.parent.parent.name,case=p.parent.name,bound=result['bound'],witnesses=len(trace['memory_witnesses']),unhookable=trace['trace_configuration']['unhookable_watches'],truncated=trace['truncated'],dropped=trace['dropped_memory_witnesses']))
 assert result['bound']
for p in sorted(s.glob('watch-*/*/*.json'))+sorted((s/'mac').glob('*/**/*.bin'))+sorted((s/'mac').glob('*/**/*.shape'))+[s/'mac/report.json']:
 target=out/'captures'/p.relative_to(s)
 target=target.with_suffix(target.suffix+'.gz');target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0) as z:z.write(p.read_bytes())
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'captures').rglob('*.gz'))}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for r in rows:print(r['name'],r['compared_bytes'],r['differing_words'],r['first'],r['original_compared_all_zero'])
print('hash-bound watches',len(summary['watches']),'archived files',len(manifest))
