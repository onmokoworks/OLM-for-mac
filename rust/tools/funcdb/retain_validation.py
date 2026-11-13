"""Retain a compact, hash-bound summary of completed local validation runs."""
from pathlib import Path
from datetime import date
import unittest
from funcdb import (HERE, DEFAULT_DB, DEFAULT_ORIGINALS, Image, digest, iter_functions,
                    read, save, stats)


def main():
    tests=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(HERE)))
    assert tests.wasSuccessful(), 'Unit tests failed'
    db=read(DEFAULT_DB)
    holdouts=read(HERE/'runs/verified/holdouts.json')
    assert len(holdouts)==10 and all(r['non_tiny_shared']>0 for r in holdouts)
    synthetic=read(HERE/'runs/verified/synthetic.json')
    assert synthetic['actual_changed_rvas']==[synthetic['expected_changed_rva']]
    relocation=read(HERE/'runs/verified/relocation.json')
    stop=read(HERE/'runs/hub-stop.json')
    assert stop['exited'] and not stop['remaining']
    for p in db['programs']:
        assert Image(DEFAULT_ORIGINALS/(p['program']+'.aex')).sha256==p['sha256']
    determinism=read(HERE/'runs/determinism.json')
    assert digest(DEFAULT_DB.read_bytes())==determinism['json_sha256']
    fs=[f for _,f,_ in iter_functions(db)]
    report=dict(date=date.today().isoformat(),platform='Windows x64 / Python 3.11 / Ghidra 12.0.3 / Capstone 5.0.7',
        unittest_passed=tests.testsRun,internal_functions=len(fs),external_functions=sum(p['external_functions'] for p in db['programs']),
        mapped_functions=len({(m['program'],m['rva']) for m in db['mappings']}),
        mapping_records=len(db['mappings']),qualified_rust_functions=sum(s['verified_rust_functions'] for s in stats(db)),
        evidence_records=len(db['evidence']),catalog=determinism,coverage=stats(db),
        decoder_warnings=dict(overlapping_functions=sum(f['decoder_overlap'] for f in fs),
                              listing_fallback_functions=sum(bool(f['listing_only_instructions']) for f in fs),
                              differing_decoded_sizes=sum(f['decoded_bytes']!=f['size'] for f in fs)),
        holdouts=[{k:v for k,v in r.items() if k!='sample'} for r in holdouts],
        synthetic={k:v for k,v in synthetic.items() if k!='changed_match'},relocation=relocation,
        shared_noise=read(HERE/'runs/shared-noise.json'),annotations=read(HERE/'runs/annotations.json'),
        hub_shutdown=stop,original_hashes_rechecked=True,
        source_sha256={p.name:digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))},
        specification_sha256={name:digest((HERE/name).read_bytes()) for name in ['reviewed.json','qualification.json','requirements.txt']})
    save(HERE/'validation.json',report)
    print('Retained validation.json; all ten original hashes rechecked')


if __name__=='__main__':
    main()
