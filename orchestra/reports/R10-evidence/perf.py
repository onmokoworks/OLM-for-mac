"""Spot-check one built fast bundle under the shared P00b benchmark lock."""
import argparse,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];S=ROOT/'orchestra/state/R10-reference-fast-split'
PROFILES={'olmdirectionalblur':('directional',['default','corpus09'],'full'),
          'radialblur':('radial',['corpus05'],'eighth'),
          'olmblur':('blur',['corpus05'],'full'),
          'olmcolorkey':('key',['corpus05'],'full'),
          'olmsmoother':('smooth',['corpus00'],'full'),
          'olmkirakira':('kira',['default','corpus05'],'full')}
p=argparse.ArgumentParser();p.add_argument('--plugin',choices=PROFILES,required=True);a=p.parse_args()
label,cases,situation=PROFILES[a.plugin];cache=S/('release-'+label);host=cache/'plugin-host'
if not host.exists():host.symlink_to(Path.home()/'.cache/olm-emu/P00b/plugin-host')
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
command=['lockf','-k',str(Path.home()/'.cache/olm-emu/bench.lock'),sys.executable,'tools/fuzz/ae_realism_audit.py','--phase','matrix','--cache',str(cache),'--state',str(S/('timing-'+label)),'--plugins',a.plugin,'--cases',*cases,'--situations',situation,'--jobs','1','--timeout','60']
with (S/('timing-'+label+'.log')).open('w') as log:subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
