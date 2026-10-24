#!/usr/bin/env python3
"""OLMBlur unittest files, isolated and serial; retain complete diagnostics."""
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
scratch = ROOT / 'orchestra/state/P01a-blur-downsample'
env = dict(os.environ, OLM_TEST_JOBS='1', TMPDIR=str(scratch), PYTHONDONTWRITEBYTECODE='1')
rows = []
for path in sorted((ROOT / 'tests').glob('test_olmblur*.py')):
    result = subprocess.run([sys.executable, '-m', 'unittest', str(path.relative_to(ROOT))],
                            cwd=ROOT, env=env, capture_output=True, text=True)
    rows.append(dict(file=str(path.relative_to(ROOT)), returncode=result.returncode,
                     stdout=result.stdout, stderr=result.stderr))
    print(path.name, result.returncode, flush=True)
(ROOT / 'orchestra/reports/P01a-evidence/unit-tests.json').write_text(json.dumps(rows, indent=2)+'\n')
sys.exit(any(row['returncode'] for row in rows))
