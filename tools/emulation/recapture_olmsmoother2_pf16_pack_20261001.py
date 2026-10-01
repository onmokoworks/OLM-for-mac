#!/usr/bin/env python3
"""Recapture the isolated writer with explicit masked, nearest-even SSE state."""
import argparse
import json
import tempfile
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_MXCSR
import probe_olmsmoother2_pf16_pack_20261001 as pack

BASELINE = pack.campaign.ROOT / 'reports/olmsmoother2_pf16_pack_baseline_20261001.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    baseline = json.loads(BASELINE.read_text())
    cases = list(pack.specifications())
    assert len(cases) == len(baseline['cases']) == baseline['case_count'] == 569
    base_loader = pack.AexLoader

    class MaskedLoader(base_loader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.uc.reg_write(UC_X86_REG_MXCSR, 0x1f80)

    pack.AexLoader = MaskedLoader
    try:
        native, mxcsr, instruction_sha = pack.native_pack(cases)
    finally:
        pack.AexLoader = base_loader
    assert mxcsr == 0x1f80
    assert instruction_sha == baseline['instruction_bytes_sha256']
    source = pack.campaign.SOURCE.read_text()
    with tempfile.TemporaryDirectory(prefix='sm2_pack16_masked_') as directory:
        binary = pack.compile_pack(Path(directory) / 'production', source, False)
        current = pack.mac_pack(binary, cases)
    for case, old, actual, production in zip(cases, baseline['cases'], native, current):
        assert case['argb_input_bits'] == old['argb_input_bits']
        assert pack.campaign.sha(actual) == old['native_raw_sha256']
        case.update(native_raw_sha256=pack.campaign.sha(actual), production_raw_sha256=pack.campaign.sha(production),
                    raw_exact=actual == production)
    deps = [Path(__file__), Path(pack.__file__), Path(pack.campaign.__file__), BASELINE,
            pack.campaign.ROOT / 'tools/emulation/aex_loader.py']
    report = {'schema': 'olmsmoother2.pf16-pack-masked-recapture/1', 'source_sha256': pack.campaign.sha(source.encode()),
              'aex_sha256': baseline['aex_sha256'], 'case_count': len(cases),
              'start_rva': baseline['start_rva'], 'stop_rva': baseline['stop_rva'],
              'instruction_bytes_sha256': instruction_sha, 'mxcsr_initial': mxcsr,
              'baseline_mxcsr_initial': baseline['mxcsr_initial'], 'native_hashes_preserved': True,
              'dependencies_sha256': {str(p.relative_to(pack.campaign.ROOT)): pack.campaign.sha(p.read_bytes()) for p in deps},
              'summary': {'raw_exact_count': sum(c['raw_exact'] for c in cases)}, 'cases': cases,
              'claims_not_made': baseline['claims_not_made'] + [
                  'MXCSR 0x1f80 is explicitly chosen for this emulated diagnostic, not read from Windows AE',
                  'The baseline loader MXCSR 0 is preserved as separate historical diagnostic evidence']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    assert report['summary']['raw_exact_count'] == len(cases)
    print('RESULT', len(cases), report['summary'], flush=True)


if __name__ == '__main__':
    main()
