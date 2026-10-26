"""Standard replay of N02 labelled cases with their original sampler flags."""
import json,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[3];E=pathlib.Path(__file__).parent;S=R/'orchestra/state/N02-olmcolorkey-nightly-20261025'
for path in sorted((R/'tests/fuzz_corpus/olmcolorkey/N02-nightly-20261025').glob('*.json')):
 d=json.loads(path.read_text());g=d.get('geometry_sampler','default');g={'realistic-v1':'realistic'}.get(g,g)
 cmd=[sys.executable,str(R/'tools/fuzz/run.py'),'--plugin','olmcolorkey','--geometry',g,'--jobs','1','--replay',str(path),'--scratch',str(S/('replay-'+path.stem)),'--report',str(E/('replay-'+path.name))]
 with (S/('replay-'+path.stem+'.log')).open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 print(path.stem,'true',flush=True)
