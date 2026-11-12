"""Hash-bound old/new PE, declaration and saved triage/funcdb review."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import pefile

CRATE = Path(__file__).resolve().parents[1]
REPO = CRATE.parents[2]
TRIAGE = REPO/'rust/tools/triage/runs/U-triage-20261112'
sys.path.insert(0,str(REPO/'rust/tools/scaffold'))
import olm_scaffold as scaffold
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base = REPO.parent
new = base/'upstream_20261112/extracted/OLMDistanceGradation/OLMDistanceGradation/Plugins/64'
paths = {'old':base/'ghidra_windows_aex/DistanceGradation.aex',
         '2025':new/'2025/DistanceGradation.aex','2026':new/'2026/DistanceGradation.aex',
         'candidate':Path(sys.argv[1]).resolve()}
records = {}
for name,path in paths.items():
    pe = pefile.PE(str(path))
    records[name] = {'sha256':digest(path),'bytes':path.stat().st_size,
        'sections':{s.Name.rstrip(b'\0').decode():hashlib.sha256(s.get_data()).hexdigest() for s in pe.sections},
        'imports':sorted(f'{d.dll.decode().lower()}!{i.name.decode() if i.name else i.ordinal}'
                         for d in pe.DIRECTORY_ENTRY_IMPORT for i in d.imports)}
    pe.close()
resources = {k:scaffold.resources(p) for k,p in paths.items()}
def pipl(r): return [x['bytes'] for x in r]
triage = json.loads((TRIAGE/'primary-DistanceGradation/triage.json').read_text())
assert triage['old']['identity']['sha256'] == records['old']['sha256']
assert triage['new']['identity']['sha256'] == records['2025']['sha256']
lookup = json.load(gzip.open(TRIAGE/'prelookup-DistanceGradation.json.gz'))
assert lookup['aex_sha256'] == records['2025']['sha256']
report = {'binaries':records,
    'new_imports':sorted(set(records['2025']['imports'])-set(records['old']['imports'])),
    'removed_imports':sorted(set(records['old']['imports'])-set(records['2025']['imports'])),
    'pipl_identical_to_2025':pipl(resources['2025']) == pipl(resources['candidate']),
    'old_new_identical_ipp_sections':{s:records['old']['sections'][s]==records['2025']['sections'][s] for s in ('IPPCODE','IPPDATA')},
    '2025_2026_identical_ipp_sections':{s:records['2026']['sections'][s]==records['2025']['sections'][s] for s in ('IPPCODE','IPPDATA')},
    'triage_sha256':digest(TRIAGE/'primary-DistanceGradation/triage.json'),
    'funcdb_sha256':digest(TRIAGE/'prelookup-DistanceGradation.json.gz'),
    'funcdb_counts':lookup['counts'],
    'reviewed_functions':[x for x in lookup['port_work'] if x['rva'] in
        ('11750f0','1174330','1174690','1171050','1171f20','1172df0','1170880','1170460','1170cc0')],
    'old_declarations_retained':json.loads((TRIAGE/'declarations/DistanceGradation/disk-id-diff.json').read_text()),
    'qualification':'Function matching is static review evidence, not a behavioral equivalence proof.'}
(CRATE/'upstream-static-report.json').write_text(json.dumps(report,indent=2))
print({k:report[k] for k in ('new_imports','removed_imports','pipl_identical_to_2025','old_new_identical_ipp_sections','funcdb_counts')})
