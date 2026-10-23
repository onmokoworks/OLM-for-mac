#!/usr/bin/env python3
"""F43 bounded double-pow diagnosis; candidates are NOT library implementations.

Uses pinned AMD source, existing PE loader and F28 native input producer.
No changes to the oracle, plugin code, or math outputs of the reference.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import struct

ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'orchestra/state/F43-ucrtmath-double'
PIN = '29fd054f383e6c5e2dec2fce781d5220059f1836'
DLL = Path.home() / '.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
DLL_HASH = '385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('variant', choices=['baseline', 'top20', 'scaled', 'combined', 'tail-fma', 'horner'])
    p.add_argument('--count', type=int, default=100_000_000)
    p.add_argument('--ranges', action='store_true')
    p.add_argument('--witness', type=int, choices=[1, 2, 3])
    a = p.parse_args()
    if a.witness:
        a.count = 1
        assert not a.ranges
    assert a.count > 0
    src = STATE / 'amd-source'
    out = STATE / ('build-' + a.variant)
    out.mkdir(parents=True, exist_ok=True)
    assert subprocess.check_output(['git', '-C', str(src), 'rev-parse', 'HEAD'], text=True).strip() == PIN
    assert not subprocess.check_output(['git', '-C', str(src), 'status', '--porcelain'], text=True).strip()
    assert sha(DLL) == DLL_HASH
    env = dict(os.environ, TMPDIR=str(out), PYTHONDONTWRITEBYTECODE='1')
    source = (src / 'src/optimized/pow.c').read_text()
    if a.variant in ('top20', 'combined', 'tail-fma', 'horner'):
        # Hypothesis: the TOP20 comparison currently uses 32 bits; using 20
        # restores nearest-integer reduction outside the exceptional range.
        old = 'int32_t abs_ylogx = (ux & ABSOLUTE_VALUE) >> 32;'
        assert source.count(old) == 1
        source = source.replace(old, old.replace('>> 32', '>> 44'))
    if a.variant in ('scaled', 'combined', 'tail-fma', 'horner'):
        # Hypothesis: rounding the reconstructed normal significand before
        # subnormal scaling loses the tail. Fuse the scaled head and tail.
        old = 'n = (int64_t)asuint64(result * dn);'
        assert source.count(old) == 1
        source = source.replace(old, 'n = (int64_t)asuint64(fma(w, dn, (z + temp) * dn));')
    if a.variant == 'tail-fma':
        old = 'double_t vt = y * log_lo + fma(y, log_hi, -v);'
        assert source.count(old) == 1
        source = source.replace(old, 'double_t vt = fma(y, log_lo, fma(y, log_hi, -v));')
    if a.variant == 'horner':
        old = 'poly = POLY_EVAL_6(r, A0, A1, A2, A3, A4, A5);'
        assert source.count(old) == 1
        source = source.replace(old, 'poly = r * (1.0 + r * (A2 + r * (A3 + r * (A4 + r * A5))));')
    (out / 'pow.c').write_text(source)
    with (out / 'build.log').open('w') as log:
        def run(cmd):
            subprocess.run(cmd, env=env, stdout=log, stderr=log, check=True)
        for mode, flags in [('off', ['-ffp-contract=off']), ('fma', ['-ffp-contract=fast', '-mfma'])]:
            run(['clang', '-arch', 'x86_64', '-O2', '-dynamiclib', *flags,
                 '-I'+str(src/'include'), '-I'+str(src/'src/optimized'), str(out/'pow.c'),
                 str(src/'src/optimized/pow_data.c'), str(src/'src/alm_special.c'),
                 '-o', str(out/f'amd-{mode}.dylib')])
        run(['clang', '-arch', 'arm64', '-O2', '-ffp-contract=off',
             str(ROOT/'ucrtmath/tests/survey_native.c'), '-o', str(out/'native')])
        run(['clang', '-arch', 'x86_64', '-O2', '-ffp-contract=off', '-Wno-deprecated-declarations',
             str(ROOT/'ucrtmath/tests/survey_compare.c'), '-o', str(out/'compare')])
    dataset = f'witness{a.witness}' if a.witness else ('ranges' if a.ranges else 'random')
    name = f'{a.variant}-{dataset}-{a.count}'
    result = STATE/(name+'.json')
    with result.open('w') as log, (STATE/(name+'.log')).open('w') as err:
        cmd = [str(out/'compare'), str(DLL), 'pow', str(out/'amd-off.dylib'), str(out/'amd-fma.dylib'), str(a.count)]
        if a.witness:
            pairs = [
                (0x4af491eedc5e5b0a, 0xc0173ef560c4bc83),
                (0x17db023316630462, 0x3f89997eeda3c17f),
                (0x300422d9a042d15f, 0x3efb46f239a9a9c7),
            ]
            # Third word is unused by UCRT/AMD pairs; Apple comparisons in
            # this single-row diagnostic are intentionally not interpreted.
            payload = struct.pack('<QQQ', *pairs[a.witness-1], 0)
            subprocess.run(cmd, input=payload, stdout=log, stderr=err, env=env, check=True)
        else:
            producer = subprocess.Popen([str(out/'native'), 'pow', str(a.count)] + (['ranges'] if a.ranges else []), stdout=subprocess.PIPE, stderr=err, env=env)
            try:
                compare = subprocess.run(cmd, stdin=producer.stdout, stdout=log, stderr=err, env=env)
                producer.stdout.close()
                rc = producer.wait()
                assert rc == compare.returncode == 0, (rc, compare.returncode)
            finally:
                if producer.poll() is None:
                    producer.kill()
                    producer.wait()
    if a.witness:
        data = json.loads(result.read_text())
        data['engines'][2] = 'unused-target-placeholder'
        data['pairs'] = [r for r in data['pairs'] if 2 not in (r['a'], r['b'])]
        result.write_text(json.dumps(data, separators=(',', ':')) + '\n')
    identity = {'amd_commit': PIN, 'dll_sha256': sha(DLL), 'variant': a.variant,
                'count': a.count, 'dataset': dataset, 'sha256': {str(f.relative_to(ROOT)): sha(f) for f in [out/'pow.c', out/'amd-off.dylib', out/'amd-fma.dylib', out/'native', out/'compare', ROOT/'ucrtmath/tests/survey_compare.c', ROOT/'ucrtmath/tests/double/diagnose.py', result]}}
    (STATE/(name+'-identity.json')).write_text(json.dumps(identity, indent=2)+'\n')
    data = json.loads(result.read_text())
    print(name, json.dumps([r for r in data['pairs'] if (r['a'],r['b']) in [(0,3),(1,4)]]))

if __name__ == '__main__':
    main()
