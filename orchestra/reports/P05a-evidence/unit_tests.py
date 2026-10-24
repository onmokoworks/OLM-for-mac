#!/usr/bin/env python3
"""Serial DirectionalBlur unittest and free-function tests; stream diagnostics."""
import argparse,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);args=ap.parse_args()
s=ROOT/'orchestra/state/P05a-directionalblur-performance'/('units-'+args.label);s.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,OLM_TEST_JOBS='1',TMPDIR=str(s),PYTHONDONTWRITEBYTECODE='1')
main='/Users/onmk/Documents/Projects/Personal/OLM as'
env['CPLUS_INCLUDE_PATH']=':'.join(main+'/'+p for p in ('Headers','Headers/SP','Util','Resources'))
rows=[]
for p in sorted(p for p in (ROOT/'tests').glob('test_*.py') if 'directionalblur' in p.name or 'dblur' in p.name):
 log=s/(p.stem+'.log')
 # unittest files and pytest-style no-argument functions both execute.
 code="import runpy,unittest; m=runpy.run_path("+repr(str(p))+",run_name='test_module'); suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(v) for v in m.values() if isinstance(v,type) and issubclass(v,unittest.TestCase)); suite.addTests(unittest.FunctionTestCase(v) for k,v in m.items() if k.startswith('test_') and callable(v)); r=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(not r.wasSuccessful())"
 with log.open('w') as f:
  result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(file=str(p.relative_to(ROOT)),returncode=result.returncode,log=str(log.relative_to(ROOT)),tail=log.read_text()[-3500:]))
 print(p.name,result.returncode,flush=True)
 (ROOT/'orchestra/reports/P05a-evidence'/('units-'+args.label+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
print('files',len(rows),'pass',sum(r['returncode']==0 for r in rows),flush=True)
