#!/usr/bin/env python3
"""Recheck real release, metadata rejection and unit contracts; no Xcode build."""
import copy
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

root = Path(__file__).resolve().parents[3]
package = Path(sys.argv[1]).resolve()
state = Path(sys.argv[2]).resolve()
state.mkdir(parents=True, exist_ok=True)
os.environ['TMPDIR'] = str(state)
tempfile.tempdir = str(state)
os.chdir(root)
suite = unittest.TestSuite()
for path in ['tests/test_verify_mac_plugin_package_hash.py', 'tests/test_release_package_layout.py', 'tests/test_release_gate_v2.py']:
    for name, obj in runpy.run_path(path).items():
        if name.startswith('test_') and callable(obj):
            suite.addTest(unittest.FunctionTestCase(obj))
        elif isinstance(obj, type) and issubclass(obj, unittest.TestCase):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(obj))
assert unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
verifier = [sys.executable, '-B', str(root/'scripts/verify_mac_plugin_package.py')]
subprocess.run(verifier + [str(package)], check=True)
manifest = json.loads(Path(str(package)+'.manifest.json').read_text())
with tempfile.TemporaryDirectory(dir=state) as tmp:
    candidate = Path(tmp)/'candidate.zip'
    shutil.copyfile(package, candidate)
    sidecar = Path(str(candidate)+'.manifest.json')
    mutations = [('missing-sidecar', None, 'could not read')]
    for field, value, message in [('binary_sha256', '0'*64, 'binary_sha256 mismatch'),
                                 ('minimum_macos', {'arm64':'10.0','x86_64':'10.0'}, 'minimum_macos mismatch'),
                                 ('signing_kind', 'unknown', 'signing_kind mismatch')]:
        altered = copy.deepcopy(manifest)
        altered['plugins'][0][field] = value
        mutations.append((field, altered, message))
    for name, data, expected in mutations:
        if data is not None:
            sidecar.write_text(json.dumps(data))
        result = subprocess.run(verifier+[str(candidate)], text=True, capture_output=True)
        assert result.returncode != 0 and expected in result.stderr, (name, result.stdout, result.stderr)
        print('REJECTED:', name, flush=True)
from intake_olm_return import package_kind
from list_olm_return_candidates import classify_zip
assert package_kind(package) == 'olm_mac_plugin_package'
assert classify_zip(package)[0] == 'mac-plugin-package'
print('PASS: real package; four negative cases; intake classification')
