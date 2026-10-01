#!/usr/bin/env python3
"""Read-only exported Smart trace of a9c0's literal-versus-LUT branch."""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image
import probe_olmsmoother2_gamma_composition_20261001 as campaign


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--trace-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert campaign.base.sha(args.worker.read_bytes()) == campaign.base.retained.FROZEN_SHA
    aex = campaign.base.retained.native_identity.AEX_PATH
    assert campaign.base.sha(aex.read_bytes()) == campaign.base.retained.native_identity.AEX_SHA256
    args.trace_dir.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGBA', (4, 3))
    image.putdata(campaign.base.retained.geometry.fixture({'geometry': [4, 3], 'pattern': 'diagonal'}))
    input_path = args.trace_dir / 'input.png'; image.save(input_path)
    encode = campaign.base.retained.campaign.retained.native_setup()[0].v2.ENCODE
    rows = []
    for version in (1, 2):
        output = args.trace_dir / f'output_v{version}.png'
        trace = args.trace_dir / f'trace_v{version}.json'
        watches = ['function=0xa9c0,arg=RCX,size=24,when=both',
                   'function=0xa9c0,arg=RCX,deref=16,size=32,when=both',
                   'function=0x4c30,arg=RCX,deref=24,size=4096,when=both',
                   'function=0xa9c0,arg=RDX,size=16,when=both']
        command = [str(args.worker), 'render-trace-png', str(aex), str(input_path), str(output),
                   '--pixel-format', 'argb32f']
        for watch in watches: command.extend(['--watch', watch])
        command.extend([f'Smoother Version={version}', 'Gamma Correction=2', 'Gamma Value=1.8',
                        'Number of Gamma Colors=1', 'Gamma Color@11=255,41,83,137'])
        result = subprocess.run(command, capture_output=True, check=True)
        trace.write_bytes(result.stdout)
        data = json.loads(result.stdout)
        assert data['render_error'] == 0 and data['guards_intact'] is True
        assert data['unsupported_suite_calls'] == [] and data['dropped_unsupported_suite_calls'] == 0
        smart = next(t for t in data['execution_traces'] if t['selector'] == 'SMART_RENDER')
        assert not smart['truncated'] and smart['dropped_memory_witnesses'] == 0
        assert smart['image_sha256'] == campaign.base.retained.native_identity.AEX_SHA256
        witnesses = smart['memory_witnesses']
        head = [w for w in witnesses if w['watch_id'] == 'watch-1']
        context = [w for w in witnesses if w['watch_id'] == 'watch-2']
        lut = [w for w in witnesses if w['watch_id'] == 'watch-3']
        gamma_lut = [w for w in lut if w['pc_rva'] in (0xaa39, 0xaa4a, 0xaa5c)]
        assert head and context
        assert all(w['before']['u32_values'][2] == (1 if version == 1 else 0) for w in head)
        assert all(w['before']['u64_values'][2] == 10000 for w in context)
        prefixes = [w['before']['sha256'] for w in gamma_lut]
        if version == 1:
            assert not gamma_lut
        else:
            assert gamma_lut
            assert set(prefixes) == {campaign.base.sha(encode[:4096])}
        rows.append({'version': version, 'render_mode': data['render_mode'],
                     'parameter_values': data['parameter_values'], 'a9c0_context_observations': len(context),
                     'internal_version_flag': 1 if version == 1 else 0, 'inverse_lut_length': 10000,
                     'gamma_color_4c30_call_observations': len(gamma_lut),
                     'gamma_color_4c30_call_rvas': sorted({hex(w['pc_rva']) for w in gamma_lut}),
                     'inverse_lut_prefix_bytes': 4096 if gamma_lut else 0,
                     'inverse_lut_prefix_sha256': sorted(set(prefixes)),
                     'input_png_sha256': campaign.base.sha(input_path.read_bytes()),
                     'local_trace_sha256': campaign.base.sha(trace.read_bytes()),
                     'raw_output_sha256': data['raw_pixel_sha256'],
                     'guards_intact': data['guards_intact'], 'unsupported_suite_calls': data['unsupported_suite_calls']})
    deps = [Path(__file__), Path(campaign.__file__), Path(campaign.base.__file__),
            Path(campaign.base.retained.campaign.retained.__file__),
            campaign.SOURCE.parent / 'OLMSmoother2_encode_lut_10000.h']
    report = {'schema': 'olmsmoother2.gamma-membership-public-route/1', 'case_count': len(rows),
              'source_sha256': campaign.base.sha(campaign.SOURCE.read_bytes()),
              'aex_sha256': campaign.base.retained.native_identity.AEX_SHA256,
              'frozen_worker_sha256': campaign.base.retained.FROZEN_SHA,
              'dependencies_sha256': {str(p.relative_to(campaign.ROOT)): campaign.base.sha(p.read_bytes()) for p in deps},
              'rows': rows, 'claims_not_made': [
                  'Different authored PNG input and exported render-trace Smart path; routing evidence, not a boundary-frame recapture',
                  'Read-only a9c0 context and 4c30 call-site snapshots from emulated AEX, not native Windows/AE',
                  'Only a 4096-byte inverse LUT prefix was read; no full 40000-byte table readback claim',
                  'Full local trace/output PNGs remain private; published report contains hashes and routing metadata',
                  'No arbitrary LUT/library/environment/UI/save/ROI/downsample or full compatibility completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('RESULT', [(r['version'], r['gamma_color_4c30_call_observations']) for r in rows], flush=True)


if __name__ == '__main__':
    main()
