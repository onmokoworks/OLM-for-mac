#!/usr/bin/env python3
"""Compare retained observations, ignoring only timings and MPFR version metadata."""
import argparse,json,pathlib

def stable(value):
 if isinstance(value,dict):return {k:stable(v) for k,v in value.items() if k not in ('seconds','gmpy2','mpfr')}
 if isinstance(value,list):return [stable(v) for v in value]
 return value

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--actual',type=pathlib.Path,required=True);ap.add_argument('--expected',type=pathlib.Path,required=True);a=ap.parse_args()
 for name in ['qualification.json','sanity.json','comparison.json','boundaries.json']:
  p=a.actual/name if name=='boundaries.json' else a.actual/'qualification'/name
  assert stable(json.loads(p.read_text()))==stable(json.loads((a.expected/name).read_text())),name
 for p in a.expected.glob('*.mismatches.jsonl'):assert p.read_bytes()==(a.actual/'qualification'/p.name).read_bytes(),p.name
 print('PASS: retained qualification, MPFR, boundary, and sample comparisons reproduce; full-domain status remains blocked')
if __name__=='__main__':main()
