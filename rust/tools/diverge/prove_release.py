"""Byte-identity experiment in a private source snapshot, never the live crates.

Winres emits HashMap-ordered VERSIONINFO and debug identities include source
checksums. Freeze identical resource inputs and disable debug output on both
release builds. No resulting DLL is patched, stripped, or normalized.
"""
import argparse
import os
from pathlib import Path
import shutil
import olm_diverge as d

PLUGINS = ('olm-directional-blur', 'olm-distance-gradation')
RUST = d.HERE.parents[1]


def source_variant(tree, enabled):
    manifest_hashes = {}
    for name in PLUGINS:
        original = RUST/'plugins'/name
        dst = tree/'rust/plugins'/name
        manifest = (original/'Cargo.toml').read_text(encoding='utf-8')
        if not enabled:
            manifest = manifest.replace('\n[features]\nstage-dump = []\n', '\n')
        (dst/'Cargo.toml').write_text(manifest, encoding='utf-8')
        for source in (original/'src').glob('*.rs'):
            text = source.read_text(encoding='utf-8')
            if not enabled and source.name == 'lib.rs':
                text = text.split('\n// Diagnostic ABI only;')[0] + '\n'
            if not enabled and source.name == 'filters.rs':
                text = text.split('\n// Diagnostic access to the retained historical arithmetic;')[0] + '\n'
            if not enabled and source.name in ('filters.rs', 'rotate.rs'):
                lines = text.splitlines(keepends=True)
                cleaned = []
                i = 0
                while i < len(lines):
                    if lines[i].strip() == '#[cfg(feature = "stage-dump")]' and i+1 < len(lines) and 'crate::stage_dump::' in lines[i+1]:
                        i += 2
                    else:
                        cleaned.append(lines[i])
                        i += 1
                text = ''.join(cleaned)
                import re
                text = re.sub(r' #\[cfg\(feature = "stage-dump"\)\] [^\n]*', '', text)
            # stage_dump.rs can remain on disk in the before snapshot: no module
            # declaration exists, so rustc cannot read or compile it.
            (dst/'src'/source.name).write_text(text, encoding='utf-8')
        manifest_hashes[name] = {p.name: d.witness.sha256(p) for p in [dst/'Cargo.toml', dst/'src/lib.rs']}
    return manifest_hashes


def prove(tree, target, out):
    tree, target, out = tree.resolve(), target.resolve(), out.resolve()
    local = (d.HERE/'local').resolve()
    if not tree.is_relative_to(local) or not (tree/'rust/Cargo.toml').exists():
        raise ValueError('tree must be an existing private build snapshot below diverge/local')
    if not target.is_relative_to(d.HERE.resolve()) or not out.is_relative_to(d.HERE.resolve()):
        raise ValueError('target and outputs must be inside diverge')
    out.mkdir(parents=True, exist_ok=False)
    report = {'qualification': 'release, debug=0, deterministic linker, identical frozen resource input; raw DLL bytes',
              'production_build_scripts_modified': False, 'resources': {}, 'builds': {}}
    for name in PLUGINS:
        dst = tree/'rust/plugins'/name
        resource = next((target/'release/build').glob(name+'-*/out/resource.lib'))
        fixed = dst/'frozen-resource.lib'
        shutil.copy2(resource, fixed)
        report['resources'][name] = d.witness.sha256(fixed)
        build = (RUST/'plugins'/name/'build.rs').read_text(encoding='utf-8')
        begin = build.index('        winres::WindowsResource::new()')
        end = build.index('            .unwrap();', begin) + len('            .unwrap();')
        replacement = '''        let out = std::path::PathBuf::from(std::env::var_os("OUT_DIR").unwrap());
        std::fs::copy("frozen-resource.lib", out.join("resource.lib")).unwrap();
        println!("cargo:rustc-link-search=native={}", out.display());
        println!("cargo:rustc-link-lib=dylib=resource");'''
        (dst/'build.rs').write_text(build[:begin]+replacement+build[end:], encoding='utf-8')
    env = {'CARGO_TARGET_DIR': str(target), 'CARGO_PROFILE_RELEASE_DEBUG': '0',
           'RUSTFLAGS': '-C link-arg=/Brepro -C link-arg=/DEBUG:NONE -C link-arg=/INCREMENTAL:NO'}
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        for label, enabled in [('before', False), ('after', True)]:
            source_hashes = source_variant(tree, enabled)
            directory = out/label
            directory.mkdir()
            command = ['cargo', 'build', '--manifest-path', str(tree/'rust/Cargo.toml'), '--release', '--offline',
                       '-p', PLUGINS[0], '-p', PLUGINS[1], '--jobs', '2']
            print('Building '+label+' (stage-dump disabled)', flush=True)
            process = d.witness.run_owned(command, 900, directory)
            report['builds'][label] = {'command': command, 'env': env, 'process': process, 'source_hashes': source_hashes, 'dlls': {}}
            if process['returncode'] or process['timeout'] or not process['cleanup_verified']:
                raise RuntimeError('release build failed; inspect '+str(directory))
            for name in PLUGINS:
                binary = target/'release'/(name.replace('-', '_')+'.dll')
                dst = directory/binary.name
                shutil.copy2(binary, dst)
                report['builds'][label]['dlls'][name] = {'sha256': d.witness.sha256(dst), 'bytes': dst.stat().st_size}
                try:
                    d.export_rva(dst, 'olm_stage_rotate_v1' if 'directional' in name else 'olm_stage_gaussian_v1')
                except ValueError:
                    pass
                else:
                    raise AssertionError('diagnostic export leaked into feature-off build')
        report['byte_identical'] = {name: (out/'before'/(name.replace('-', '_')+'.dll')).read_bytes() ==
                                   (out/'after'/(name.replace('-', '_')+'.dll')).read_bytes() for name in PLUGINS}
        if not all(report['byte_identical'].values()):
            raise AssertionError('raw release DLL bytes differ')
        print('PASS: both complete release DLLs are byte-identical', flush=True)
        return report
    finally:
        # Restore the private snapshot to current sources/build scripts. Production
        # paths have only been read, and no cache or task output is deleted.
        source_variant(tree, True)
        for name in PLUGINS:
            shutil.copy2(RUST/'plugins'/name/'build.rs', tree/'rust/plugins'/name/'build.rs')
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        d.write_json(out/'proof.json', report)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tree', required=True, type=Path)
    p.add_argument('--target', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    prove(a.tree, a.target, a.out)
