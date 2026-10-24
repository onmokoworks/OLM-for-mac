#!/usr/bin/env python3
"""Record why final equality cannot refresh the legacy typed-plane assertions."""
import hashlib,json,struct,subprocess,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R05-regenerate-stale-bindings'
WORKER=Path('/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker')
SOURCE=Path('/Users/onmk/.cache/olm-emu/src-F46/reference-guest/crates/aex-guest-worker/src/main.rs')
build=json.loads(Path('/Users/onmk/.cache/olm-emu/F46-pow-build.json').read_text())
sha=lambda raw:hashlib.sha256(raw).hexdigest()
assert sha(SOURCE.read_bytes())==build['source_manifest']['crates/aex-guest-worker/src/main.rs']
command=[str(WORKER),'session',str(ROOT.parent.parent/'aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex'),str(S/'unused-input.raw'),str(S/'unused-output.raw'),'9','7','24','--pixel-format','argb32f','--watch','function=0x4640,arg=rcx,size=16']
proc=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(S/'F46-session-watch.log').write_text(proc.stdout)
assert proc.returncode==2 and 'usage:' in proc.stdout
f49_recipe=ROOT/'tools/emulation/aexcompat_patches/build_F49.py'
assert 'function_rva: Some(0x1ec0)' in f49_recipe.read_text()
samples=[]
for p in sorted((ROOT/'refs/fixtures/olmradialblur_F39_F32_final_20261023').glob('*/provenance.json')):
    row=json.loads(p.read_text());raw=zlib.decompress(p.with_name('source.argb.zlib').read_bytes())
    fmt='H' if row['depth']==16 else 'f'
    promoted={((v*32768+127)//255 if fmt=='H' else struct.unpack('<f',struct.pack('<f',v/255))[0]) for v in range(256)}
    values=[v[0] for v in struct.iter_unpack('<'+fmt,raw)]
    samples.append(dict(index=row['command_index'],source_sha256=sha(raw),nonrepresentable_samples=sum(v not in promoted for v in values)))
assert all(r['nonrepresentable_samples']>0 for r in samples)
(S/'trace-capability.json').write_text(json.dumps(dict(command=command,exit=proc.returncode,worker_sha256=sha(WORKER.read_bytes()),source_sha256=sha(SOURCE.read_bytes()),source_manifest_verified=True,f49_recipe_sha256=sha(f49_recipe.read_bytes()),f49_boundary='Existing F49 workers hardcode DirectionalBlur rotation RVA 0x1ec0; they do not provide configurable Radial plane watches.',samples=samples,boundary='F46 session parser rejects --watch; render-trace-png converts to RGBA8 before typed promotion. No typed intermediate reference was obtained.'),indent=2)+'\n')
print('F46 typed trace unavailable; all 14 checked typed inputs lose samples through PNG promotion')
