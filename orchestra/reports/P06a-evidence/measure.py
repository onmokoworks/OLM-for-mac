"""Build this plugin only and run the P00b performance driver, serially."""
import argparse,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P06a-directionalblur-pf32-cropped-mismatch'
E=ROOT/'orchestra/reports/P06a-evidence'
a=argparse.ArgumentParser();a.add_argument('--label',required=True);a.add_argument('--build',action='store_true');args=a.parse_args()
b=S/args.label;b.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
if args.build:
 with (S/('build-'+args.label+'.log')).open('w') as log:subprocess.run([sys.executable,'tools/fuzz/build_F47_bundles.py','--plugins','OLMDirectionalBlur','--scratch',str(b)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
host=b/'plugin-host'
if not host.exists():host.symlink_to(Path.home()/'.cache/olm-emu/P00b/plugin-host')
cmd=[sys.executable,'tools/fuzz/ae_realism_audit.py','--phase','matrix','--cache',str(b),'--state',str(S/('timing-'+args.label)),'--plugins','olmdirectionalblur','--cases','default','corpus09','--situations','full','4k','--jobs','1','--timeout','60']
with (S/('timing-'+args.label+'.log')).open('w') as log:subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
for name in ('matrix.jsonl','matrix-manifest.json'):(E/(args.label+'-'+name)).write_bytes((S/('timing-'+args.label)/name).read_bytes())
print(args.label,'timing complete',flush=True)
