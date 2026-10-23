#!/usr/bin/env python3
"""Compile the exact native Win64 callbacks in isolation and compare raw bits.

This checks the production callback body/ABI without claiming that the full
native-carrier backend (which has separate host-interface gaps) is qualified.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
S = ROOT/'orchestra/state/F45-integrate-ms-double'
SOURCE = Path.home()/'.cache/olm-emu/src-F45/reference-guest'
DLL = Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
env = dict(os.environ, TMPDIR=str(S), TMP=str(S), TEMP=str(S), OLM_UCRT_FMA='1')
pressure = subprocess.check_output(['memory_pressure'], text=True)
free = int(re.search(r'System-wide memory free percentage: (\d+)%', pressure)[1])
assert free >= 30, f'Build blocked at {free}% free'
manifest = json.loads((ROOT/'orchestra/reports/F45-evidence/build-manifest.json').read_text())
for relative, expected in manifest['source_manifest'].items():
    assert hashlib.sha256((SOURCE/relative).read_bytes()).hexdigest() == expected, relative
imports = (SOURCE/'crates/aex-guest-worker/src/native_x64/imports.rs').read_text()
functions = ['sin', 'cos', 'exp']
wrappers = []
for fn in functions:
    assert f'| "{fn}"' in imports
    assert f'"{fn}" => callback_address!(native_{fn})' in imports
    body = re.search(r'pub\(super\) unsafe extern "win64" fn native_'+fn+r'\(value: f64\) -> f64 \{[^}]+\}', imports)[0]
    wrappers.append(body.replace('pub(super)', 'pub'))
module = SOURCE/'crates/olm-ucrtmath/src/lib.rs'
program = '#[path = '+json.dumps(str(module))+']\nmod olm_ucrtmath;\n'+'\n'.join(wrappers)+r'''
fn main() {
    use std::io::Write;
    let args: Vec<String> = std::env::args().collect();
    let callback: unsafe extern "win64" fn(f64) -> f64 = match args[1].as_str() {
        "sin" => native_sin, "cos" => native_cos, "exp" => native_exp,
        _ => panic!("unknown function"),
    };
    let count: u64 = args[2].parse().unwrap();
    let mut out = std::io::BufWriter::new(std::io::stdout().lock());
    for i in 0..count {
        let mut z = (i ^ 0xf45).wrapping_add(0x9e3779b97f4a7c15);
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
        z ^= z >> 31;
        let (a,b) = (z, 0u64);
        let result = unsafe { callback(f64::from_bits(a)) }.to_bits();
        for word in [a,b,result,result] { out.write_all(&word.to_le_bytes()).unwrap(); }
    }
    out.flush().unwrap();
}
'''
(S/'native_probe.rs').write_text(program)
with (S/'native-build.log').open('w') as log:
    subprocess.run(['sh', str(SOURCE/'crates/olm-ucrtmath/ucrtmath/build.sh'), str(S/'native-lib'), 'x86_64'], env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    subprocess.run(['rustc', '--edition=2024', '--target', 'x86_64-apple-darwin', '-O', str(S/'native_probe.rs'), '-L', 'native='+str(S/'native-lib'), '-l', 'static=ucrtmath', '-o', str(S/'native-probe')], env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
rows = []
for fn in functions:
    stream = S/'native-stream.bin'
    with stream.open('wb') as output:
        subprocess.run(['/usr/bin/arch', '-x86_64', str(S/'native-probe'), fn, '1000000'], env=env, stdout=output, check=True)
    with stream.open('rb') as inp, (S/'native-oracle.log').open('a') as log:
        result = subprocess.run(['/usr/bin/arch', '-x86_64', str(S/'compare'), str(DLL), fn, '1', '1000000'], env=env, stdin=inp, stdout=subprocess.PIPE, stderr=log, text=True, check=True)
    stream.unlink()
    row = json.loads(result.stdout)
    rows.append(row)
    print(fn, row['count'], row['mismatches'], flush=True)
(ROOT/'orchestra/reports/F45-evidence/native-shim-results.json').write_text(json.dumps({'memory_free_percent': free, 'native_probe_sha256': hashlib.sha256((S/'native-probe').read_bytes()).hexdigest(), 'results': rows}, indent=2)+'\n')
