#!/usr/bin/env python3
"""Verify all complete sweep evidence byte-for-byte, including bucket sums."""
import argparse,csv,gzip,io,pathlib
p=argparse.ArgumentParser();p.add_argument('--actual',type=pathlib.Path,required=True);p.add_argument('--expected',type=pathlib.Path,required=True);a=p.parse_args()
for fn in ('expf','sinf','cosf','atan2f','powf'):
 expected_count=100000000 if fn in ('atan2f','powf') else 1<<32
 data={}
 for kind in ('counts','buckets','first'):
  raw=(a.actual/fn/f'{kind}.csv').read_bytes()
  assert raw==gzip.decompress((a.expected/f'{fn}-{kind}.csv.gz').read_bytes()),(fn,kind)
  data[kind]=list(csv.DictReader(io.StringIO(raw.decode())))
 assert len(data['counts'])==10
 for row in data['counts']:
  assert int(row['processed'])==expected_count
  n=int(row['mismatches']);assert 0<=n<=expected_count
  for arg in ('0','1'):
   assert sum(int(r['mismatches']) for r in data['buckets'] if r['pair']==row['pair'] and r['argument']==arg)==n
  assert sum(r['pair']==row['pair'] for r in data['first'])==min(2000,n)
 print(f'PASS {fn}: {expected_count} inputs, all 10 pairs, buckets and first mismatches exact')
