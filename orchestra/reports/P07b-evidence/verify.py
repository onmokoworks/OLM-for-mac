"""Read-only check of retained P07b evidence and its current source binding."""
import hashlib,json,re,statistics
from pathlib import Path
root=Path(__file__).resolve().parents[3];e=Path(__file__).resolve().parent
def read(name):return json.loads((e/name).read_text())
source='mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
sha=hashlib.sha256((root/source).read_bytes()).hexdigest()
assert read('thread-build.json')['source_sha256']==sha
for name in ('diff','diff-default'):
 assert read(name+'-builds.json')['fast']['sources'][source]==sha
 summary=read(name+'-summary.json');assert summary['counts']['mismatch']==0
 for line in (e/(name+'-results.jsonl')).read_text().splitlines():
  row=json.loads(line)
  assert set(row['fast'])=={'1','2','8'}
  assert all(v['first_mismatch'] is None and v['sha256']==row['reference']['sha256'] and v['error']==row['reference']['error'] for v in row['fast'].values())
exact=refusal=0
for name in ('default','realistic-1','realistic-20261025','realistic-v2-1','realistic-v2-20261025','odd-even'):
 report=read(name+'.json');assert report['status']=='complete' and report['completed']==report['requested']
 for row in report['cases']:
  smart=row['result']['routes']['smart'];oracle=row['result']['oracles']['smart']
  if smart['status']=='exact':
   exact+=1;assert smart['raw_sha256']==oracle['raw_sha256']
  else:
   refusal+=1;assert smart['status']=='refusal' and oracle['status']=='reject'
assert (exact,refusal)==(701,149)
assert sum(read('replay-'+str(n)+'.json')['completed'] for n in (256,623))==15
assert all(read('replay-'+str(n)+'.json')['replay_matches_saved'] for n in (256,623))
threads=read('threads-results.json');assert len(threads)==100
for i in range(50):
 runs=threads[i]['runs']+threads[50+i]['runs']
 assert all(v['result']['status']=='ok' for v in runs)
 assert len({v['sha256'] for v in runs})==1
assert read('units-before-sdk/results.json')==read('units-after/results.json')
for p in (e/'units-after').glob('*.log'):
 assert re.findall(r'^(?:ERROR|FAIL):.*$',p.read_text(),re.M)==re.findall(r'^(?:ERROR|FAIL):.*$',(e/'units-before-sdk'/p.name).read_text(),re.M)
rows=read('concurrent-results.json')+read('concurrent-recheck.json')
for size in {(v['width'],v['height']) for v in rows}:
 assert len({v['sha256'] for v in rows if (v['width'],v['height'])==size})==1
for w in (256,1920):
 r=read('concurrent-recheck.json')
 med=lambda cap:statistics.median(v['four_seconds'] for v in r if v['width']==w and v['cap']==cap)
 assert med(8)<med(1)
print('P07b evidence OK: 850 AEX cases, 15 replays, 96 reference/fast comparisons, 50 forced-cap + 50 TSan cases; unchanged unit failures; concurrent hashes match and cap-8 median improves.')
