#!/usr/bin/env python3
"""Build the isolated F47d shared-arena/native bridge; cache is read-only."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[3] / "tools/ucrt_cxx.py")
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STATE = ROOT/'orchestra/state/F47d-native-plugin-all'
PARENT = Path.home()/'.cache/olm-emu/src-F47'

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    global STATE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=STATE)
    parser.add_argument('--target', choices=('aarch64-apple-darwin', 'x86_64-apple-darwin'), default='aarch64-apple-darwin')
    parser.add_argument('--cache-name', default=None, help='Install and register a new durable worker')
    parser.add_argument('--build-root', type=Path, default=Path.home()/'Documents/Projects/Personal/04_Tools/AEXCompat-build-F47d')
    args = parser.parse_args()
    STATE = args.state.resolve()
    if args.target == 'x86_64-apple-darwin':
        STATE = STATE/'x86_64'
    STATE.mkdir(parents=True,exist_ok=True)
    cache = Path.home()/'.cache/olm-emu'
    build = cache/('build-'+(args.cache_name or 'F47d'))
    tmp = build/'tmp'; tmp.mkdir(parents=True, exist_ok=True)
    source = args.build_root.resolve()
    if source.exists():
        raise RuntimeError(f'build source already exists: {source}')
    if any(c in str(source) for c in ' :'):
        raise ValueError('Unicorn source path must not contain spaces or colons')
    env=dict(os.environ,TMPDIR=str(tmp),TMP=str(tmp),TEMP=str(tmp),CARGO_BUILD_JOBS='1',
        CMAKE_BUILD_PARALLEL_LEVEL='1',CARGO_TARGET_DIR=str(build/'target'),AEXCOMPAT_BUILD_REVISION=args.cache_name or 'F47d-native-all')
    try:
        if source.exists(): shutil.rmtree(source)
        shutil.copytree(PARENT,source)
        cmake=source/'vendor/unicorn-engine-sys/CMakeLists.txt'
        body=cmake.read_text()
        old='execute_process(COMMAND sh ${CMAKE_CURRENT_SOURCE_DIR}/qemu/configure'
        assert body.count(old)==1
        cmake.write_text(body.replace(old,'execute_process(COMMAND ${CMAKE_COMMAND} -E env "PWD=${CMAKE_BINARY_DIR}" sh ${CMAKE_CURRENT_SOURCE_DIR}/qemu/configure'))
        crate=source/'crates/aex-guest-worker'
        lib=crate/'src/lib.rs'
        body=lib.read_text().replace('forbid(unsafe_code)','deny(unsafe_code)')
        lib.write_text(body+'\n#[cfg(target_os = "macos")]\n#[allow(unsafe_code)]\nmod native_bridge;\n')
        shutil.copy2(HERE/'F47d-native-ffi.rs',crate/'src/native_bridge.rs')
        classic=crate/'src/classic.rs'
        body=classic.read_text()
        marker='    fn render_smart(\n'
        assert body.count(marker)==1
        body=body.replace(marker,(HERE/'F47d-native-render.rs').read_text()+'\n'+marker)
        marker='            if smart_render {\n'
        assert body.count(marker)==1
        body=body.replace(marker,'''            #[cfg(target_os = "macos")]
            if let Ok(path) = std::env::var("OLM_NATIVE_BUNDLE_EXECUTABLE") {
                if backend.is_gpu() || census_enabled || trace_enabled {
                    return Err(ClassicError::Input("native bridge supports CPU without census/trace only".into()));
                }
                return self.render_native_bundle(&path, params, input_param, output_world, format, output_request, smart_render);
            }
'''+marker)
        classic.write_text(body)
        # Audit every shared constant read by the Rust bridge against the SDK.
        constants=dict(re.findall(r'pub const (\w+): usize = (\d+);',(PARENT/'crates/aex-abi/src/generated.rs').read_text()))
        names=set(re.findall(r'abi::([A-Z0-9_]+)',(HERE/'F47d-native-render.rs').read_text()+(HERE/'F47d-native-ffi.rs').read_text()))
        sizes={'PF_IN_DATA_SIZE':'PF_InData','PF_PARAM_DEF_SIZE':'PF_ParamDef','PF_LAYER_DEF_SIZE':'PF_LayerDef'}
        probe=['#include "AEConfig.h"','#include "AE_Effect.h"','#include <cstddef>']
        for name in sorted(names):
            if name in sizes: expr=f'sizeof({sizes[name]})'
            else:
                prefix,field=name.split('_',1)
                typ={'IN':'PF_InData','PARAM':'PF_ParamDef','LAYER':'PF_LayerDef'}[prefix]
                expr=f'offsetof({typ}, {field.removesuffix("_OFFSET").lower()})'
            probe.append(f'static_assert({expr} == {constants[name]}, "{name}");')
        (STATE/'abi.cpp').write_text('\n'.join(probe))
        with (STATE/'bridge-build.log').open('w') as log:
            for src,out in [(STATE/'abi.cpp',STATE/'abi.o'),(HERE/'F47d-native-bridge.cpp',STATE/'bridge.o')]:
                subprocess.run([_UCRT_CXX,'-arch', 'x86_64' if args.target.startswith('x86') else 'arm64','-std=c++17','-Wno-pragma-pack','-I'+str(ROOT/'Headers'),'-I'+str(ROOT/'Headers/SP'),'-c',str(src),'-o',str(out)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            subprocess.run(['ar','rcs',str(STATE/'libf47c.a'),str(STATE/'bridge.o')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        build=crate/'build.rs'
        body=build.read_text().replace('fn main() {','fn main() {\n    println!("cargo:rustc-link-search=native='+str(STATE)+'");\n    println!("cargo:rustc-link-lib=static=f47c");\n    println!("cargo:rustc-link-lib=c++");',1)
        build.write_text(body)
        pressure=subprocess.check_output(['memory_pressure'],text=True)
        (STATE/'memory-pressure.log').write_text(pressure)
        free=int(re.search(r'System-wide memory free percentage: (\d+)%',pressure)[1])
        if free<30: raise RuntimeError(f'memory pressure: {free}% free')
        command=['cargo','build','--manifest-path',str(source/'Cargo.toml'),'--release','--target',args.target,'--offline','--locked','-j','1','-p','aex-guest-worker','--bin','aex-guest-worker']
        with (STATE/'rust-build.log').open('w') as log:
            subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        worker=STATE/'aex-guest-worker'
        shutil.copy2(build/'target'/args.target/'release/aex-guest-worker',worker)
        result=dict(worker_sha256=sha(worker),abi_constants=len(names),memory_free_percent=free,command=command,
            sources={p.name:sha(p) for p in HERE.glob('F47d-*')})
        (STATE/'build.json').write_text(json.dumps(result,indent=2)+'\n')
        if args.cache_name:
            import fcntl
            dest=cache/args.cache_name
            dest.mkdir(exist_ok=False)
            shutil.copy2(worker,dest/'aex-guest-worker')
            result.update(name=args.cache_name, worker_path=str(dest/'aex-guest-worker'),
                          recipe='tools/emulation/aexcompat_patches/build_F47d.py',
                          build_json=str(dest/'build.json'))
            (dest/'build.json').write_text(json.dumps(result,indent=2)+'\n')
            with (cache/'.index.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX)
                index_path=cache/'INDEX.json'; index=json.loads(index_path.read_text())
                assert not any(r['name']==args.cache_name for r in index['links'])
                index['links'].append(result)
                index_path.write_text(json.dumps(index,indent=2)+'\n')
        print(json.dumps(result))
    finally:
        shutil.rmtree(build,ignore_errors=True)
        shutil.rmtree(source,ignore_errors=True)

if __name__=='__main__': main()
