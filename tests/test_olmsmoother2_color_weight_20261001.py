"""Current-source replay of colored AEX scans and the exported Smart owner."""
import importlib
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/emulation'))
campaign = importlib.import_module('probe_olmsmoother2_color_weight_20261001')
geometry = importlib.import_module('probe_olmsmoother2_color_scan_geometry_20261001')
public = importlib.import_module('replay_olmsmoother2_exported_color_weight_20261001')


def bound_capture(name):
    path = ROOT / 'reports' / name
    data = json.loads(path.read_text())
    assert len(data['cases']) == data['case_count']
    assert data['aex_sha256'] == public.owner.native_identity.AEX_SHA256
    # These native captures keep their historical production source identity.
    assert data['source_sha256'] == 'b1cd2a4dfebe7c94cd22dddd9e7bfa355faf7564af7ae7f15732d3a7eb11d871'
    for dependency, expected in data['dependencies_sha256'].items():
        assert campaign.retained.sha((ROOT / dependency).read_bytes()) == expected, dependency
    return data


def replay_internal_current_source():
    base = {kind: bound_capture(f'olmsmoother2_color_weight_{kind}_20261001.json')
            for kind in ('dispatch', 'controls')}
    observed = bound_capture('olmsmoother2_color_weight_actual_dispatch_20261001.json')
    large = bound_capture('olmsmoother2_color_scan_geometry_20261001.json')
    assert [base[k]['case_count'] for k in ('dispatch', 'controls')] == [512, 2688]
    assert observed['case_count'] == 3200 and large['case_count'] == 144
    paired = list(zip(observed['cases'], base['dispatch']['cases'] + base['controls']['cases']))
    assert len(paired) == 3200
    method_differences = 0
    for actual, old in paired:
        for key in ('target_index', 'profile', 'depth', 'version', 'smoothing',
                    'input_sha256', 'native_raw_sha256'):
            assert actual[key] == old[key], key
        assert actual['raw_exact'] and actual['class_exact'] and actual['actual_dispatch_exact']
        if actual['actual_native_dispatch_histogram'] != actual['baseline_class_derived_histogram']:
            method_differences += 1
            assert actual['smoothing'][0] == 0
            assert actual['actual_native_dispatch_histogram'] == {}
    assert method_differences == 384  # theoretical indices differ from executed dispatches
    total = 0
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    with tempfile.TemporaryDirectory(prefix='sm2_color_weight_regression_') as directory:
        for sanitize in (False, True):
            binary = campaign.compile_harness(Path(directory) / ('san' if sanitize else 'o2'),
                                              campaign.SOURCE.read_text(), sanitize)
            for actual, old in paired:
                pixels = campaign.fixture(old['target_index'], old['profile'])
                assert campaign.retained.sha(campaign.retained.typed_input(pixels, old['depth'])) == old['input_sha256']
                output, plane, hist = campaign.production(binary, old, env)
                assert campaign.retained.sha(output) == old['native_raw_sha256']
                assert campaign.retained.sha(plane) == old['native_class_plane_sha256']
                assert hist == {int(k): v for k, v in actual['actual_native_dispatch_histogram'].items()}
                total += 1
            for case in large['cases']:
                assert case['raw_exact'] and case['class_exact'] and case['actual_dispatch_exact']
                typed = campaign.retained.typed_input(geometry.fixture(case), case['depth'])
                assert campaign.retained.sha(typed) == case['input_sha256']
                output, plane, hist = geometry.production(binary, case, env)
                assert campaign.retained.sha(output) == case['native_raw_sha256']
                assert campaign.retained.sha(plane) == case['native_class_plane_sha256']
                assert hist == {int(k): v for k, v in case['native_dispatch_histogram'].items()}
                total += 1
            print('SM2_INTERNAL_CURRENT_REPLAY', 'san' if sanitize else 'o2', total, flush=True)
    assert total == 6688


class ColorWeightTests(unittest.TestCase):
    def test_internal_current_source(self):
        replay_internal_current_source()

    def test_public_current_source(self):
        data = public.replay(campaign.SOURCE.read_text())
        self.assertEqual(data['render_count'], 504)
        self.assertEqual(data['summary']['raw_exact_count'], 504)

    def test_prerender_positive_dimensions_and_invalid_host_authority(self):
        program = '''
#include "production_under_test.cpp"
static int w, h, calls;
static bool wrong_ref;
static PF_Err checkout(PF_ProgPtr, A_long index, A_long id, PF_RenderRequest *req,
                       A_long, A_long, A_long, PF_CheckoutResult *r) {
    ++calls;
    if (index != SM_INPUT || id != SM_INPUT || req->rect.left != 0 || req->rect.top != 0 ||
        req->rect.right != w || req->rect.bottom != h || !req->preserve_rgb_of_zero_alpha) return 91;
    r->ref_width = wrong_ref ? w + 1 : w; r->ref_height = h;
    r->result_rect = r->max_result_rect = {0,0,0,0};
    return 0;
}
int main() {
    const int sizes[][2] = {{1,1},{1,9},{9,1},{2,2},{15,16},{16,15},{16,16}};
    for (const auto &size : sizes) for (short depth : {8,16,32}) {
        w = size[0]; h = size[1];
        PF_InData in{}; PF_OutData out{}; in.width=w; in.height=h;
        in.downsample_x={1,1}; in.downsample_y={1,1};
        PF_PreRenderInput input{}; input.bitdepth=depth;
        PF_PreRenderOutput output{}; PF_PreRenderCallbacks cb{&checkout};
        PF_PreRenderExtra extra{&input,&output,&cb};
        calls=0;
        if (EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&extra) || calls != 1) return 10;
        if (output.result_rect.left || output.result_rect.top || output.result_rect.right != w ||
            output.result_rect.bottom != h || !(output.flags & PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS)) return 11;
        for (int invalid=0; invalid<6; ++invalid) {
            PF_InData bad=in; PF_PreRenderOutput rejected{}, pristine{};
            PF_PreRenderExtra bx{&input,&rejected,&cb}; calls=0;
            if (invalid==0) bad.width=0;
            if (invalid==1) bad.height=-1;
            if (invalid==2) bad.width=8193;
            if (invalid==3) bad.height=8193;
            if (invalid==4) bad.downsample_x={1,2};
            if (invalid==5) bad.downsample_y={0,0};
            if (!EffectMain(PF_Cmd_SMART_PRE_RENDER,&bad,&out,nullptr,nullptr,&bx) || calls ||
                memcmp(&rejected,&pristine,sizeof(rejected))) return 20+invalid;
        }
        PF_PreRenderOutput rejected{}, pristine{}; PF_PreRenderExtra bx{&input,&rejected,&cb};
        calls=0; wrong_ref=true;
        if (!EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&bx) || calls!=1 ||
            memcmp(&rejected,&pristine,sizeof(rejected))) return 30;
        wrong_ref=false;
    }
    return 0;
}
'''
        with tempfile.TemporaryDirectory(prefix='sm2_prerender_authority_') as directory:
            path = Path(directory)
            (path / 'production_under_test.cpp').write_text(campaign.SOURCE.read_text())
            source = path / 'probe.cpp'; source.write_text(program)
            binary = path / 'probe'
            subprocess.run(['clang++', '-std=c++17', '-O1', '-g', '-fsanitize=address,undefined',
                            '-fno-omit-frame-pointer', '-Wno-deprecated-declarations',
                            '-I', str(path), '-I', str(ROOT / 'cli/OLMSmoother2/shim'),
                            '-I', str(campaign.SOURCE.parent), str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, env=dict(os.environ,
                           ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1'))


if __name__ == '__main__':
    unittest.main()
