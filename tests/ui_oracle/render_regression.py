#!/usr/bin/env python3
"""Sequential default fuzz and pinned-worker corpus replay for U04's touched plugins."""
import argparse,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PLUGINS=['colorkeep','olmcolorkey','olmsmoother2','olmkirakira','radialblur']
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scratch',type=Path,required=True);ap.add_argument('--phase',choices=['fuzz','corpus'],required=True);ap.add_argument('--only',choices=PLUGINS);args=ap.parse_args()
    state=args.scratch.resolve();state.mkdir(parents=True,exist_ok=True);summary=[]
    for plugin in ([args.only] if args.only else PLUGINS):
        report=state/(plugin+'-'+args.phase+'.json')
        cmd=['python3',str(ROOT/'tools/fuzz/run.py'),'--plugin',plugin,'--n','300','--seed','1','--jobs','1','--scratch',str(state/(plugin+'-scratch')),'--report',str(report),'--corpus',str(state/(plugin+'-generated'))]
        if args.phase=='corpus':
            inputs=state/(plugin+'-inputs');inputs.mkdir(exist_ok=True)
            for folder in sorted((ROOT/'tests/fuzz_corpus').glob(plugin+'*')):
                for path in sorted(folder.glob('*.json')):
                    link=inputs/(folder.name+'__'+path.name)
                    if not link.exists():link.symlink_to(path)
            cmd+=['--replay',str(inputs)]
        with (state/(plugin+'-'+args.phase+'.log')).open('w') as log:
            run=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=log,env={**os.environ,'TMPDIR':str(state)})
        summary.append({'plugin':plugin,'returncode':run.returncode,'report':str(report)})
        print(json.dumps(summary[-1]),flush=True)
    (state/(args.phase+'-runs.json')).write_text(json.dumps(summary,indent=2)+'\n')
    return int(any(x['returncode'] for x in summary))
if __name__=='__main__':raise SystemExit(main())
