#!/usr/bin/env python3
"""Run the unchanged F54b corpus comparisons in F54c scratch, one process at a time."""
import argparse, collections, gzip, hashlib, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F54c-aexcompat-resident-watches'
PLUGINS=['olmblur','colorkeep','olmcolorkey','olmdirectionalblur','olmdistancegradation','olmkirakira','olmsmoother2','olmtoondilate','radialblur','olmsmoother']
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    S.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
    for key in list(env):
        if key.startswith('AEXCOMPAT_RESIDENT_') or key.startswith('AEXCOMPAT_SMART_TRACE'): del env[key]
    totals=collections.Counter();summaries={}
    with gzip.open(S/'corpus-results.jsonl.gz','wt') as retained:
        for plugin in PLUGINS:
            d=S/f'corpus-{plugin}'
            if not (args.resume and (d/'summary.json').exists()):
                (d/'summary.json').unlink(missing_ok=True)
                with (S/f'corpus-{plugin}.log').open('w') as log:
                    result=subprocess.run([sys.executable,str(Path(__file__).with_name('verify_F54b.py')),'--worker',str(args.worker),'--plugin',plugin,'--jobs','1','--scratch-root',str(S)],env=env,stdout=log,stderr=subprocess.STDOUT)
                if result.returncode and not (d/'summary.json').exists():
                    raise SystemExit(f'{plugin}: driver failed before summary')
            summary=json.loads((d/'summary.json').read_text());summaries[plugin]=summary
            def file_sha(path):
                with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
            assert summary['worker_sha256']==file_sha(args.worker)
            assert summary['baseline_sha256']==file_sha(Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker')
            expected=set()
            for p in (ROOT/'tests/fuzz_corpus').glob(plugin+'*/**/*.json'):
                if json.loads(p.read_text()).get('plugin')!=plugin:continue
                for route in (['classic'] if plugin=='olmsmoother' else ['classic','smart']):expected.add(str(p.relative_to(ROOT/'tests/fuzz_corpus'))+'/'+route)
            seen=set();observed_counts=collections.Counter()
            for line in (d/'results.jsonl').open():
                row=json.loads(line);assert row['case'] not in seen;seen.add(row['case']);observed_counts[row['category']]+=1
                retained.write(json.dumps(dict(plugin=plugin,**row))+'\n')
            assert seen==expected,(plugin,len(seen),len(expected))
            assert len(seen)==summary['cases']
            for category,count in observed_counts.items():assert summary[category]==count
            totals.update({k:summary[k] for k in ['cases','exact_ok','matching_non_success','byte_difference','status_difference']})
            (S/'corpus-summary.json').write_text(json.dumps(dict(plugins=summaries,totals=dict(totals)),indent=2)+'\n')
            print(plugin,dict(totals),flush=True)
    if totals['byte_difference'] or totals['status_difference']:raise SystemExit(1)
if __name__=='__main__':main()
