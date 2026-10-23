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
S = ROOT/'orchestra/state/F46-integrate-ucrt-pow'
SOURCE = Path.home()/'.cache/olm-emu/src-F46/reference-guest'
DLL = Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
env = dict(os.environ, TMPDIR=str(S), TMP=str(S), TEMP=str(S), OLM_UCRT_FMA='1')
pressure = subprocess.check_output(['memory_pressure'], text=True)
free = int(re.search(r'System-wide memory free percentage: (\d+)%', pressure)[1])
assert free >= 30, f'Build blocked at {free}% free'
manifest = json.loads((ROOT/'orchestra/reports/F46-evidence/build-manifest.json').read_text())
for relative, expected in manifest['source_manifest'].items():
    assert hashlib.sha256((SOURCE/relative).read_bytes()).hexdigest() == expected, relative
imports = (SOURCE/'crates/aex-guest-worker/src/native_x64/imports.rs').read_text()
functions = ['pow']
wrappers = []
for fn in functions:
    assert f'| "{fn}"' in imports
    assert f'"{fn}" => callback_address!(native_{fn})' in imports
    body = re.search(r'pub\(super\) unsafe extern "win64" fn native_'+fn+r'\(left: f64, right: f64\) -> f64 \{[^}]+\}', imports)[0]
    wrappers.append(body.replace('pub(super)', 'pub'))
module = SOURCE/'crates/olm-ucrtmath/src/lib.rs'
program = '#[path = '+json.dumps(str(module))+']\nmod olm_ucrtmath;\n'+'\n'.join(wrappers)+r'''
fn main() {
    use std::io::Write;
    let args: Vec<String> = std::env::args().collect();
    let callback: unsafe extern "win64" fn(f64, f64) -> f64 = match args[1].as_str() {
        "pow" => native_pow,
        _ => panic!("unknown function"),
    };
    let count: u64 = args[2].parse().unwrap();
    let mut out = std::io::BufWriter::new(std::io::stdout().lock());
    for i in 0..count {
        fn mix(mut z: u64) -> u64 {
            z = z.wrapping_add(0x9e3779b97f4a7c15);
            z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
            z ^ (z >> 31)
        }
        let (x,y) = (mix(i ^ 0xf46), mix(i ^ 0x706f77));
        // Plugin ranges: normalized/HDR bases, sRGB gamma and repeat exponents.
        let (a,b) = if std::env::var("F46_RANGE").as_deref() == Ok("plugin") {
            let base = (x >> 11) as f64 / 9007199254740992.0;
            let exponent = match i % 4 { 0 => 2.4, 1 => 1.0/2.4,
                2 => (y % 100) as f64, _ => (y >> 11) as f64 / 9007199254740992.0 * 10.0 };
            ((if i % 8 == 0 {base * 16.0} else {base}).to_bits(), exponent.to_bits())
        } else { (x,y) };
        let result = unsafe { callback(f64::from_bits(a), f64::from_bits(b)) }.to_bits();
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
for domain in ['random','plugin']:
    fn='pow'; env['F46_RANGE']=domain
    stream = S/'native-stream.bin'
    with stream.open('wb') as output:
        subprocess.run(['/usr/bin/arch', '-x86_64', str(S/'native-probe'), fn, '1000000'], env=env, stdout=output, check=True)
    with stream.open('rb') as inp, (S/'native-oracle.log').open('a') as log:
        result = subprocess.run(['/usr/bin/arch', '-x86_64', str(S/'compare'), str(DLL), fn, '1', '1000000'], env=env, stdin=inp, stdout=subprocess.PIPE, stderr=log, text=True, check=True)
    stream.unlink()
    row = json.loads(result.stdout); row["domain"] = domain
    rows.append(row)
    print(fn, row['count'], row['mismatches'], flush=True)
(ROOT/'orchestra/reports/F46-evidence/native-shim-results.json').write_text(json.dumps({'memory_free_percent': free, 'native_probe_sha256': hashlib.sha256((S/'native-probe').read_bytes()).hexdigest(), 'results': rows}, indent=2)+'\n')
