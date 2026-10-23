#!/usr/bin/env python3
"""Compact hash-bound census from the C23 ticket-local campaign reports."""
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--scratch',type=Path,default=ROOT/'orchestra/state/C23-smoother2-colorkeep-toondilate-fresh')
p.add_argument('--report',type=Path,default=ROOT/'orchestra/reports/C23-fresh-census.json')
a=p.parse_args(); rows=[]
for plugin in ('olmsmoother2','colorkeep','olmtoondilate'):
    for seed in range(1 if plugin=='olmsmoother2' else 2,7):
        path=a.scratch/f'{plugin}-seed{seed}.json'; data=json.loads(path.read_text())
        assert data['completed']==data['requested']==300 and data['status']=='complete'
        cases=data['cases']; residual=[c for c in cases if c['result']['routes']['smart']['status']!='exact']
        rows.append({'plugin':plugin,'seed':seed,'summary':data['summary'],
            'campaign_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'provenance':data['provenance'],'smart_residuals':residual,
            'input_hashes':[c['input_sha256'] for c in cases],
            'smart_output_hashes':[c['result']['routes']['smart'].get('raw_sha256') for c in cases]})
a.report.write_text(json.dumps({'scope':'CPU AEX Smart versus public SDK shim; fresh seed 2-6 plus Smoother2 seed 1','campaigns':rows},indent=2,sort_keys=True)+'\n')
for row in rows: print(row['plugin'],row['seed'],{k:v for k,v in row['summary'].items() if k.startswith('smart')})
