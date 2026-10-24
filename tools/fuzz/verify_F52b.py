#!/usr/bin/env python3
"""Compare corpus reconstruction with the F52b starting commit (no renders)."""
import importlib
import json
from pathlib import Path
import subprocess
import types
from types import SimpleNamespace

from core import load_corpus, sha
from run import ROOT, main_checkout

BASE = '22f8f8023645f6299abe6a19f2f596eae7157148'


def main():
    baseline = types.ModuleType('f52b_baseline_core')
    source = subprocess.check_output(['git','show',BASE+':tools/fuzz/core.py'],cwd=ROOT)
    exec(compile(source,'baseline-core.py','exec'),baseline.__dict__)
    rows = []
    for path in sorted((ROOT/'tests/fuzz_corpus').glob('*/*.json')):
        data = json.loads(path.read_text())
        a = importlib.import_module('adapters.'+data['plugin']).Adapter(SimpleNamespace(
            max_size=data['max_size'],case_timeout=10,main=main_checkout(),worker=Path('/usr/bin/true')))
        before,_ = baseline.load_corpus(path,a)
        after,_ = load_corpus(path,a)
        if before != after:
            raise AssertionError(str(path))
        rows.append((str(path.relative_to(ROOT)),sha(after['pixels'])))
    print(json.dumps({'baseline':BASE,'reconstructed':len(rows),'identical':len(rows),
                      'path_input_hash_manifest_sha256':sha(json.dumps(rows,separators=(',',':')).encode()),
                      'rendered':0},indent=2))


if __name__ == '__main__':
    main()
