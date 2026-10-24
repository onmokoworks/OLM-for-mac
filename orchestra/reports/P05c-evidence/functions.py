"""Run module-level test functions that unittest discovery does not collect."""
import importlib.util,inspect,os,subprocess,sys,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
if sys.argv[1]=='--module':
 p=Path(sys.argv[2]);scratch=Path(sys.argv[3]);sys.path.insert(0,str(ROOT))
 spec=importlib.util.spec_from_file_location(p.stem,p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 if hasattr(module,'SCRATCH'):module.SCRATCH=scratch
 suite=unittest.TestSuite()
 for name,fn in inspect.getmembers(module,inspect.isfunction):
  if not name.startswith('test_'):continue
  parameters=inspect.signature(fn).parameters
  if not parameters:suite.addTest(unittest.FunctionTestCase(fn))
  elif list(parameters)==['tmp_path']:suite.addTest(unittest.FunctionTestCase(lambda fn=fn:fn(scratch)))
  else:raise RuntimeError((name,str(parameters)))
 result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())
plugin,label=sys.argv[1:]
s=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance'/label;s.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1');rows=[]
for p in sorted((ROOT/'tests').glob('test_'+plugin+'*.py')):
 if plugin=='olmsmoother' and p.name.startswith('test_olmsmoother2'):continue
 if '\ndef test_' not in p.read_text():continue
 with (s/(p.stem+'.log')).open('w') as log:r=subprocess.run([sys.executable,__file__,'--module',str(p),str(s)],env=env,stdout=log,stderr=subprocess.STDOUT)
 rows.append(dict(file=str(p.relative_to(ROOT)),returncode=r.returncode))
(s/'summary.json').write_text(json.dumps(rows,indent=2)+'\n');print('modules',len(rows),'failed',sum(x['returncode']!=0 for x in rows))
