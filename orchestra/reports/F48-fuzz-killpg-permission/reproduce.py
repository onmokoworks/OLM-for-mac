"""F48 reproduction: default real race probe; --baseline injects both OS errors."""
from collections import Counter
from pathlib import Path
import subprocess
import sys
import time
import types
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
import core

if '--baseline' in sys.argv:
    import test_timeout_cleanup
    source = subprocess.check_output(['git', 'show',
        'd6cd18daa05d1106718faa2594d4fe7a3b089564:tools/fuzz/core.py'], cwd=ROOT, text=True)
    baseline = types.ModuleType('baseline')
    exec(compile(source, 'baseline_core.py', 'exec'), baseline.__dict__)
    core.command = baseline.command
    suite = unittest.TestSuite([test_timeout_cleanup.CleanupTests('test_live_child_pid_fallback')])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print('EXPECTED REPRODUCTION:', len(result.errors), 'errors')
    assert len(result.errors) == 2
else:
    counts, examples = Counter(), {}
    for _ in range(200):
        result, _, _ = core.command(['/usr/bin/true'], timeout=.000001, deadline=time.monotonic()+2)
        cleanup = result.get('cleanup')
        key = str((result['status'], cleanup['status'] if cleanup else 'no diagnostic'))
        counts[key] += 1
        if cleanup:
            examples[key] = result
    print(dict(counts))
    print(examples)
