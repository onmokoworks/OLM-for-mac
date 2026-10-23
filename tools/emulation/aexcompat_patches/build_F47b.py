#!/usr/bin/env python3
"""Build the opt-in F47b OLMBlur lifecycle probe in ticket-local scratch."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[3] / "tools/ucrt_cxx.py")
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STATE = ROOT / 'orchestra/state/F47b-native-plugin-host-render'
PARENT = Path.home() / '.cache/olm-emu/src-F47'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_abi(env):
    """Every shared ABI constant consumed by the native shim gets an SDK check."""
    body = (HERE / 'F47b-native-host.rs').read_text()
    names = sorted(set(re.findall(r'abi::([A-Z0-9_]+)', body)))
    generated = (PARENT / 'crates/aex-abi/src/generated.rs').read_text()
    constants = dict(re.findall(r'pub const (\w+): usize = (\d+);', generated))
    structs = {'PF_IN_DATA_SIZE': 'PF_InData', 'PF_OUT_DATA_SIZE': 'PF_OutData',
               'PF_UTIL_CALLBACKS_SIZE': 'PF_UtilCallbacks', 'PF_PARAM_DEF_SIZE': 'PF_ParamDef'}
    special = {'PARAM_UU_OFFSET': 'uu', 'PARAM_PARAM_TYPE_OFFSET': 'param_type',
               'IN_PICA_BASICP_OFFSET': 'pica_basicP'}
    commands = {'GLOBAL_SETUP', 'PARAMS_SETUP', 'SEQUENCE_SETUP', 'SEQUENCE_SETDOWN', 'GLOBAL_SETDOWN'}
    lines = ['#include "AEConfig.h"', '#include "AE_Effect.h"', '#include "AE_EffectCB.h"',
             '#include "SPErrorCodes.h"', '#include <cstdio>', '#include <cstddef>',
             'static_assert(sizeof(PF_Err) == 4);',
             'static_assert(PF_Err_BAD_CALLBACK_PARAM == 516);',
             "static_assert(kSPSuiteNotFoundError == 0x53214664);"]
    lines.append('int main() {')
    for name in names:
        if name in structs:
            expr = 'sizeof(' + structs[name] + ')'
        elif name.startswith('PF_CMD_') and name[7:] in commands:
            expr = 'PF_Cmd_' + name[7:]
        else:
            prefix, tail = name.split('_', 1)
            typename = {'IN': 'PF_InData', 'OUT': 'PF_OutData', 'INTER': 'PF_InteractCallbacks',
                        'PARAM': 'PF_ParamDef'}[prefix]
            field = special.get(name, tail.rsplit('_', 1)[0].lower())
            expr = f'offsetof({typename}, {field})'
            if name.endswith('_SIZE'):
                expr = f'sizeof((({typename}*)0)->{field})'
        lines.append(f'printf("{name} %zu\\n", size_t({expr}));')
    lines.append('}')
    probe = STATE / 'abi.cpp'
    probe.write_text('\n'.join(lines) + '\n')
    cmd = [_UCRT_CXX, '-Wno-pragma-pack', '-I' + str(ROOT / 'Headers'),
           '-I' + str(ROOT / 'Headers/SP'), str(probe), '-o', str(STATE / 'abi')]
    with (STATE / 'abi-build.log').open('w') as log:
        subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    output = subprocess.check_output([str(STATE / 'abi')], env=env, text=True)
    (STATE / 'mac-abi.txt').write_text(output)
    actual = dict(line.split() for line in output.splitlines())
    expected = {name: constants[name] for name in names}
    if actual != expected:
        raise RuntimeError(f'Mac/shared ABI differs: {actual} != {expected}')
    return len(names)


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TMPDIR=str(STATE), TMP=str(STATE), TEMP=str(STATE),
               CARGO_BUILD_JOBS='1', CMAKE_BUILD_PARALLEL_LEVEL='1',
               CARGO_TARGET_DIR=str(STATE / 'target'), AEXCOMPAT_BUILD_REVISION='F47b-lifecycle')
    # A no-space alias keeps Unicorn's configure source path valid while all
    # scratch bytes remain in the ticket's worktree. Never copy to the cache.
    alias = Path.home() / '.cache/olm-emu/F47b-scratch-link'
    if alias.is_symlink():
        if alias.resolve() != STATE:
            raise RuntimeError('F47b scratch alias belongs to another worktree')
    elif alias.exists():
        raise RuntimeError('F47b scratch alias is occupied')
    else:
        alias.symlink_to(STATE, target_is_directory=True)
    env['CARGO_TARGET_DIR'] = str(alias / 'target')
    count = verify_abi(env)
    source = STATE / 'source'
    if source.exists():
        shutil.rmtree(source)
    shutil.copytree(PARENT, source)
    # CMake chdir loses the logical alias in a child shell unless PWD is
    # explicitly supplied. This changes build plumbing, not Unicorn code.
    cmake = source / 'vendor/unicorn-engine-sys/CMakeLists.txt'
    original = cmake.read_text()
    old = 'execute_process(COMMAND sh ${CMAKE_CURRENT_SOURCE_DIR}/qemu/configure'
    assert original.count(old) == 1
    cmake.write_text(original.replace(old,
        'execute_process(COMMAND ${CMAKE_COMMAND} -E env "PWD=${CMAKE_BINARY_DIR}" sh ${CMAKE_CURRENT_SOURCE_DIR}/qemu/configure'))
    base = Path('crates/aex-guest-worker/src')
    path = source / base / 'main.rs'
    original_main = path.read_text()
    body = original_main.replace('mod native_plugin;', 'mod native_plugin;\n#[cfg(target_os = "macos")]\nmod native_host;', 1)
    old = '''        if args.next().as_deref() != Some(std::ffi::OsStr::new("--inspect")) || args.next().is_some() {'''
    new = '''        let mode = args.next();
        let setup = mode.as_deref() == Some(std::ffi::OsStr::new("--setup"));
        if (!setup && mode.as_deref() != Some(std::ffi::OsStr::new("--inspect"))) || args.next().is_some() {'''
    assert old in body
    body = body.replace(old, new, 1).replace('BUNDLE --inspect; render/session unsupported', 'BUNDLE --inspect|--setup; render/session unsupported', 1)
    body = body.replace('native_plugin::inspect(&path)', 'native_plugin::inspect(&path, setup)', 1)
    old_result = 'Ok(report) => { println!("{report}"); ExitCode::SUCCESS }'
    new_result = 'Ok(report) => { let failed = report.get("setup_ok").and_then(|v| v.as_bool()) == Some(false); println!("{report}"); if failed { ExitCode::from(1) } else { ExitCode::SUCCESS } }'
    assert old_result in body
    body = body.replace(old_result, new_result, 1)
    path.write_text(body)
    diff = ''.join(difflib.unified_diff(original_main.splitlines(True), body.splitlines(True),
                                      'a/' + str(base / 'main.rs'), 'b/' + str(base / 'main.rs')))
    path = source / base / 'native_plugin.rs'
    original_plugin = path.read_text()
    body = original_plugin.replace('pub fn inspect(path: &Path)', 'pub fn inspect(path: &Path, setup: bool)', 1)
    body = body.replace('    let mut resources = Vec::new();', '''    // Unsupported tables remain absent; constrain this prototype to the audited plugin.
    if setup && path.file_name().and_then(|n| n.to_str()) != Some("OLMBlur.plugin") {
        return Err("native setup prototype supports OLMBlur.plugin only".into());
    }
    let mut resources = Vec::new();''', 1)
    body = body.replace('        Ok(\n            json!(', '        let mut report = json!(', 1)
    old = '''"selectors_executed":[], "render_supported":false}),
        )'''
    new = '''"selectors_executed":[], "render_supported":false});
        if setup {
            let pointer = CFBundleGetFunctionPointerForName(bundle.0, name.0);
            let lifecycle = crate::native_host::setup(pointer)?;
            report["capability"] = json!("olmblur-lifecycle-only");
            for (key, value) in lifecycle.as_object().unwrap() {
                report[key] = value.clone();
            }
        }
        Ok(report)'''
    assert old in body
    body = body.replace(old, new, 1)
    path.write_text(body)
    diff += ''.join(difflib.unified_diff(original_plugin.splitlines(True), body.splitlines(True),
                                       'a/' + str(base / 'native_plugin.rs'), 'b/' + str(base / 'native_plugin.rs')))
    (STATE / 'integration.patch').write_text(diff)
    shutil.copy2(HERE / 'F47b-native-host.rs', source / base / 'native_host.rs')
    pressure = subprocess.check_output(['memory_pressure'], text=True)
    (STATE / 'memory-pressure.log').write_text(pressure)
    free = int(re.search(r'System-wide memory free percentage: (\d+)%', pressure)[1])
    if free < 30:
        raise RuntimeError(f'Build blocked: {free}% free, need 30%')
    cmd = ['cargo', 'build', '--manifest-path', str(alias / 'source/Cargo.toml'), '--release',
           '--offline', '--locked', '-j', '1', '-p', 'aex-guest-worker', '--bin', 'aex-guest-worker']
    try:
        with (STATE / 'rust-build.log').open('w') as log:
            subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        worker = STATE / 'aex-guest-worker'
        shutil.copy2(STATE / 'target/release/aex-guest-worker', worker)
        manifest = dict(worker_sha256=sha(worker), shared_abi_sha256=sha(PARENT / 'crates/aex-abi/src/generated.rs'),
                        native_host_sha256=sha(HERE / 'F47b-native-host.rs'),
                        parent_loader_sha256=sha(PARENT / base / 'native_plugin.rs'),
                        native_main_sha256=sha(source / base / 'main.rs'),
                        integration_patch_sha256=sha(STATE / 'integration.patch'),
                        recipe_sha256=sha(Path(__file__)),
                        sdk_hashes={name: sha(ROOT / name) for name in
                            ('Headers/AE_Effect.h', 'Headers/AE_EffectCB.h', 'Headers/SP/SPErrorCodes.h')},
                        checked_abi_constants=count, memory_free_percent=free,
                        command=cmd, capability='olmblur-lifecycle-only')
        (STATE / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(json.dumps(manifest))
    finally:
        shutil.rmtree(STATE / 'target', ignore_errors=True)
        shutil.rmtree(source, ignore_errors=True)


if __name__ == '__main__':
    main()
