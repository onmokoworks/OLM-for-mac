#!/usr/bin/env python3
"""Bounded first-parent regression probe: real self-test, mocked work execution."""
import argparse,importlib.util,json,os,subprocess,sys,types,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--expect-head-pass', action='store_true', help='verify a repaired HEAD while retaining the historical good/bad controls')
parser.add_argument('--scratch-dir', type=Path, default=ROOT/'orchestra/state/I02-integration-finish')
args=parser.parse_args()
S=args.scratch_dir.resolve()
S.mkdir(parents=True, exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1')
import tempfile
tempfile.tempdir=str(S)
path=ROOT/'tests/test_run_olm_generic_beta_gate.py'
spec=importlib.util.spec_from_file_location('i02_selftest',path)
tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
merge='dd7d8fa1'
revisions=[merge+'^1',merge,'HEAD']
results=[]
for rev in revisions:
    revision=subprocess.check_output(['git','rev-parse',rev],cwd=ROOT,text=True).strip()
    source=subprocess.check_output(['git','show',revision+':scripts/run_olm_generic_beta_gate.py'],cwd=ROOT,text=True)
    gate=types.ModuleType('i02_gate_'+revision)
    gate.__file__=str(ROOT/'scripts/run_olm_generic_beta_gate.py')
    exec(compile(source,gate.__file__,'exec'),gate.__dict__)
    tests.GATE=gate
    os.environ['OLM_SELF_SPAWN_CHILD']='1'
    suite=unittest.TestSuite([tests.GenericBetaGateTests('test_main_publishes_running_before_execution_then_final_same_run_id')])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    results.append(dict(revision=revision,success=result.wasSuccessful(),tests=result.testsRun,errors=[text for _,text in result.errors],failures=[text for _,text in result.failures]))
(S/'gate-self-bisect.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps([{'revision':r['revision'],'success':r['success']} for r in results]))
sys.exit(0 if [r['success'] for r in results]==[True,False,args.expect_head_pass] else 1)
