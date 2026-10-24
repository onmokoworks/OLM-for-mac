#!/usr/bin/env python3
"""Serial replay of every DirectionalBlur corpus, including nested witnesses."""
import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P02j-directionalblur-geometry'
E=ROOT/'orchestra/reports/P02j-evidence'
os.environ.update(TMPDIR=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
paths=sorted({p.parent for p in (ROOT/'tests/fuzz_corpus').rglob('*.json') if 'olmdirectionalblur' in str(p)})
for corpus in paths:
 name='-'.join(corpus.relative_to(ROOT/'tests/fuzz_corpus').parts)
 runner='orchestra/reports/P02j-evidence/replay_realistic.py' if 'realistic_P02j' in name else 'tools/fuzz/run.py'
 cmd=[sys.executable,runner,'--plugin','olmdirectionalblur','--jobs','1','--replay',str(corpus),'--scratch',str(S/'replay'),'--report',str(E/('replay-'+name+'.json'))]
 with (S/('replay-'+name+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 print(name,r.returncode,flush=True)
