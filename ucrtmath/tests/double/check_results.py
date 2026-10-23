#!/usr/bin/env python3
"""Verify reproduced numerical evidence, excluding unstable binary hashes."""
import json
from pathlib import Path
here = Path(__file__).resolve().parent
state = here.parents[2] / 'orchestra/state/F43-ucrtmath-double'
expected = json.loads((here/'results.json').read_text())
for campaign in expected['campaigns']:
    actual = json.loads((state/(campaign['name']+'.json')).read_text())
    pairs = [r for r in actual['pairs'] if (r['a'], r['b']) in [(0,3), (1,4)]]
    assert actual['count'] == campaign['count'], campaign['name']
    assert pairs == campaign['pairs'], campaign['name']
    identity = json.loads((state/(campaign['name']+'-identity.json')).read_text())
    source_hash = next(v for k,v in identity['sha256'].items() if k.endswith('/pow.c'))
    assert source_hash == campaign['candidate_source_sha256'], campaign['name']
    assert identity['dll_sha256'] == expected['dll_sha256']
    assert identity['amd_commit'] == expected['amd_commit']
print('6 campaigns: numerical results, candidate source hashes, AMD/DLL pins match')
