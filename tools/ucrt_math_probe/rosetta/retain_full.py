#!/usr/bin/env python3
"""Package small CSV evidence deterministically; checkpoints remain scratch."""
import argparse,csv,gzip,json,pathlib,re,hashlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--state',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();summary={}
for fn in ('expf','sinf','cosf','atan2f','powf'):
 d=a.state/'full'/fn;expected=100000000 if fn in ('atan2f','powf') else 1<<32
 counts=list(csv.DictReader((d/'counts.csv').open()));assert all(int(r['processed'])==expected for r in counts)
 for kind in ('counts','buckets','first'):
  (a.out/f'{fn}-{kind}.csv.gz').write_bytes(gzip.compress((d/f'{kind}.csv').read_bytes(),mtime=0))
 log=(a.state/'full'/f'{fn}.log').read_text();progress=re.findall(r'next=(\d+) elapsed=([\d.]+) inputs=(\d+)',log)
 pilot=(a.state/f'pilot-{fn}.log').read_text();timing=re.search(r'elapsed=([\d.]+)',pilot)
 summary[fn]=dict(processed=expected,counts={r['pair']:int(r['mismatches']) for r in counts},pilot_seconds=float(timing[1]),pilot_projected_seconds=float(timing[1])*expected/(1<<24),progress=progress[-1],stub_counts=re.findall(r'STUB ([^\n]+)',log)[-1])
summary['provenance']=dict(host=subprocess.check_output(['sw_vers'],text=True).strip(),compiler=subprocess.check_output(['clang','--version'],text=True).splitlines()[0],binary_hashes={name:hashlib.sha256((a.state/name).read_bytes()).hexdigest() for name in ['sweep','amd/amd-off.dylib','amd/amd-fma.dylib']},dll_sha256='385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3',amd_commit='29fd054f383e6c5e2dec2fce781d5220059f1836',seed='0xf27c',rng='SplitMix64(n XOR seed): low/high 32 bits, n starts at 0',order=['ucrt0','ucrt1','apple','amd-off','amd-fma'],unary='n=0..2^32-1, exact bits including NaNs',bucket='(input_bits >> 23) & 255; sign combined; binary argument 0 and 1 marginals',pairwise='raw output bits; NaN sign and payload differences count as mismatches',chunks=1<<24)
(a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
