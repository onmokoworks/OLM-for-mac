#!/usr/bin/env python3
"""Verify the explicitly load-only F47 boundary against three real bundles."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[3] / "tools/ucrt_cxx.py")
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
S = ROOT / 'orchestra/state/F47-aexcompat-native-plugin-host'
WORKER = Path.home() / '.cache/olm-emu/worker-F47-nativeplugin/aex-guest-worker'

def main():
    env = dict(os.environ, TMPDIR=str(S), TMP=str(S), TEMP=str(S))
    results = []
    for name in ('OLMBlur', 'OLMColorKey', 'OLMRadialBlur'):
        bundle = S / f'xcode/{name}/products/{name}.plugin'
        cmd = [str(WORKER), 'native-plugin', str(bundle), '--inspect']
        run = subprocess.run(cmd, env=env, text=True, capture_output=True, check=True)
        result = json.loads(run.stdout)
        assert result['entrypoint_resolved'] is True
        assert result['entrypoint'] == 'EffectMain'
        assert result['render_supported'] is False
        assert result['selectors_executed'] == []
        result['command'] = cmd
        results.append(result)
        rejected = subprocess.run(cmd[:-1], env=env, capture_output=True)
        assert rejected.returncode == 2, rejected
    (S / 'loader-results.json').write_text(json.dumps(results, indent=2) + '\n')
    cmd = [_UCRT_CXX, '-Wno-pragma-pack', '-I' + str(ROOT / 'Headers'),
           '-I' + str(ROOT / 'Headers/SP'), str(Path(__file__).with_name('F47-abi-probe.cpp')),
           '-o', str(S / 'abi')]
    subprocess.run(cmd, env=env, check=True)
    result = subprocess.check_output([str(S / 'abi')], env=env, text=True)
    expected = {
        'PF_InData': 408, 'PF_OutData': 408, 'PF_ParamDef': 176,
        'PF_LayerDef': 120, 'PF_InteractCallbacks': 176,
        'PF_InData.utils': 176, 'PF_InData.effect_ref': 184,
        'PF_InData.pica_basicP': 384, 'PF_ParamDef.u': 56, 'PF_LayerDef.data': 24,
    }
    observed = {line.rsplit(' ', 1)[0]: int(line.rsplit(' ', 1)[1])
                for line in result.splitlines()}
    assert observed == expected, (observed, expected)
    (S / 'mac-abi.txt').write_text(result)
    print('3/3 bundles loaded and EffectMain resolved; 3/3 unsupported render invocations rejected')
    print(result, end='')

if __name__ == '__main__':
    main()
