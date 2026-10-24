#!/usr/bin/env python3
"""Package only diagnostic records, never regenerable products or binaries."""
import argparse, hashlib, json, tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R07-gate-contracts-and-bindings'
OUT=ROOT/'orchestra/reports'
p=argparse.ArgumentParser();p.add_argument('group',choices=['contracts','f40','bindings']);args=p.parse_args()
files=[S/f'{args.group}.json',*sorted(S.glob(f'{args.group}-*.log'))]
if args.group=='f40':
 files += [p for p in sorted((S/'colorkeep-oracle').glob('*')) if p.is_file()]
 files += [p for p in sorted(S.glob('blur-*')) if p.is_file()]
 files += [p for p in sorted((S/'blur-owner').rglob('*')) if p.is_file() and not any(part.startswith('build-') for part in p.parts)]
 files += [S/'f40-adjudication.json']
if args.group=='bindings':
 files += [p for p in sorted(S.glob('performance-*')) if p.is_file()]
rows=[]
archive=OUT/f'R07-{args.group}-evidence.tar.xz'
with tarfile.open(archive,'w:xz') as tar:
 for path in files:
  with path.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
  name=str(path.relative_to(S));tar.add(path,arcname=name)
  rows.append(dict(path=name,sha256=digest,bytes=path.stat().st_size))
with archive.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
(OUT/f'R07-{args.group}-manifest.json').write_text(json.dumps(dict(archive=archive.name,sha256=digest,files=rows),indent=2)+'\n')
print(args.group,len(rows),archive.stat().st_size,digest)
