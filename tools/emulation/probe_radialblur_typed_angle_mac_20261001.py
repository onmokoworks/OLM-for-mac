#!/usr/bin/env python3
"""Current public Mac replay of independently traced typed Angle/Offset rows."""
import argparse
import json
from pathlib import Path
import tempfile

import probe_radialblur_public_aligned_20261001 as public

CAPTURE = public.ROOT/'reports/radialblur_typed_angle_public_route_20261001.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    capture = json.loads(CAPTURE.read_text())
    rows = []
    with tempfile.TemporaryDirectory(prefix='radial_typed_mac_capture_') as directory:
        temp = Path(directory)
        binary = public.build(temp/'o2', public.SOURCE.read_text())
        for index, case in enumerate(capture['rows']):
            results = {}
            for command in ('classic', 'smart'):
                error, raw, metadata = public.mac_render(binary, temp, case, command)
                results[command] = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                                    'raw_exact': not error and public.sha(raw) == case['native_raw_sha256'],
                                    'metadata': metadata}
            rows.append({'row_index': index, 'native_raw_sha256': case['native_raw_sha256'],
                         'input_sha256': case['input_sha256'], 'results': results})
    summary = {'both_commands_exact': sum(all(r['raw_exact'] for r in row['results'].values()) for row in rows),
               'different': sum(not row['results']['classic']['error'] and not row['results']['classic']['raw_exact'] for row in rows),
               'mac_rejected': sum(bool(row['results']['classic']['error']) for row in rows)}
    dependencies = [Path(__file__), CAPTURE, public.SOURCE, public.initial.HARNESS,
                    public.SOURCE.parent/'OLMRadialBlur.h', Path(public.__file__), Path(public.initial.__file__),
                    public.ROOT/'core/dblur_noise.h', public.ROOT/'core/olm_sha256_rows.h']
    report = {'schema': 'radialblur.typed-angle-public-mac/1', 'case_count': len(rows), 'rows': rows,
              'source_sha256': public.sha(public.SOURCE.read_bytes()), 'summary': summary,
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in dependencies},
              'claims_not_made': ['Noise Offset remains unrestored', 'Remaining raw mismatches are not accepted as completion',
                                 'No installed/native Windows AE/UCRT equivalence or full compatibility proof']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('RESULT', summary, flush=True)


if __name__ == '__main__':
    main()
