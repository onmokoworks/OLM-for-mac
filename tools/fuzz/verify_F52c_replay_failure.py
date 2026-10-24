#!/usr/bin/env python3
"""Check the new default replay failure with the unchanged pre-ticket adapter."""
import json,subprocess,time,types,sys
from pathlib import Path
from types import SimpleNamespace
from core import load_corpus,sha
from run import main_checkout
from measure_F52c import ROOT,S
START='ef2b582f'
def main():
 current='--current' in sys.argv
 source=(ROOT/'tools/fuzz/adapters/radialblur.py').read_text() if current else subprocess.check_output(['git','show',START+':tools/fuzz/adapters/radialblur.py'],cwd=ROOT,text=True)
 module=types.ModuleType('adapters.f52c_baseline_radial');module.__file__=str(ROOT/'tools/fuzz/adapters/radialblur.py');module.__package__='adapters';exec(compile(source,module.__file__,'exec'),module.__dict__)
 path=ROOT/'tests/fuzz_corpus/radialblur/C49_seed1_case000117.json';data=json.loads(path.read_text())
 a=module.Adapter(SimpleNamespace(main=main_checkout(),worker=Path(data['provenance']['worker_path']),max_size=data['max_size'],case_timeout=data['provenance']['case_timeout_seconds']))
 s=S/'baseline-failure';s.mkdir(exist_ok=True);a.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
 case,_=load_corpus(path,a);r,raw=a.oracle(case,s,time.monotonic()+90,'smart')
 report=dict(baseline_commit='current' if current else START,adapter_sha256=sha(source.encode()),worker_sha256=sha(a.worker.read_bytes()),case=str(path.relative_to(ROOT)),input_sha256=sha(case['pixels']),result=r,output_sha256=sha(raw))
 (S/('current-failure.json' if current else 'baseline-failure.json')).write_text(json.dumps(report,indent=2)+'\n');print(r['status'],r.get('diagnostic','')[:240])
if __name__=='__main__':main()
