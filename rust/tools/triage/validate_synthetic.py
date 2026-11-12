"""Build two isolated Rust OLMBlur derivatives; never edit production sources.

The only source difference is 2.0f32 -> 3.0f32 inside triage_legacy_amount.
Defaults are identical; only enabling Legacy exposes the changed multiplier.
"""
import argparse
import json
from pathlib import Path
import shutil

import olm_triage as t


def build_pair(out):
    rust = t.HERE.parent.parent
    source = rust / "plugins" / "olm-blur" / "src"
    out.mkdir(parents=True, exist_ok=False)
    pipl_dir = out / "rust-pipl"
    pipl_dir.mkdir()
    # Only a Rust-produced resource is copied. Original AEX files stay external.
    pe = t.pe_inventory(rust / "target" / "release" / "olm_blur.dll", pipl_dir)
    pipl = (pipl_dir / pe["pipl"][0]["raw_file"]).read_bytes()
    builds = []
    target = out / "target"
    source_root = out / "source"
    source_root.mkdir()
    shutil.copytree(source, source_root / "src")
    for name, constant in (("old", "2.0"), ("new", "3.0")):
        root = source_root
        result = out / name
        result.mkdir()
        ae = (source / "ae.rs").read_text(encoding="utf-8")
        needle = "amount: v[0].number as f32,"
        assert ae.count(needle) == 1
        ae = ae.replace(needle, "amount: triage_legacy_amount(v[0].number as f32, v[4].number != 0.0),")
        ae += f'''\n#[no_mangle]\n#[inline(never)]\npub extern "C" fn triage_legacy_amount(amount: f32, legacy: bool) -> f32 {{
    if legacy && amount <= 100.0 {{ amount * {constant}f32 }} else {{ amount }}
}}\n'''
        (root / "src" / "ae.rs").write_text(ae, encoding="utf-8")
        (result / "ae.rs").write_text(ae, encoding="utf-8")
        (root / "effect.pipl").write_bytes(pipl)
        manifest = '''[package]
name = "triage-synthetic-blur"
version = "0.0.0"
edition = "2021"
publish = false
[workspace]
[lib]
crate-type = ["cdylib"]
[dependencies]
'''
        for crate in ("olm-core", "olm-math", "olm-ae"):
            manifest += f'{crate} = {{ path = "{(rust / "crates" / crate).as_posix()}" }}\n'
        manifest += '[build-dependencies]\nwinres = "0.1"\n[profile.release]\ndebug = 0\n'
        (root / "Cargo.toml").write_text(manifest, encoding="utf-8")
        (root / "build.rs").write_text('''fn main() {
    let p = std::path::PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").unwrap()).join("effect.pipl");
    winres::WindowsResource::new().append_rc_content(&format!("16000 PiPL DISCARDABLE \\\"{}\\\"", p.display().to_string().replace('\\\\', "/"))).compile().unwrap();
}
'''.replace('\\\\\\"', '\\"'), encoding="utf-8")
        command = ["cargo", "build", "--offline", "--release", "--jobs", "2", "--manifest-path", root / "Cargo.toml", "--target-dir", target]
        print(f"Building synthetic {name}", flush=True)
        process = t.oracle.run_process(command, 600)
        t.oracle.write_json(result / "build.process.json", process)
        if process["returncode"] or process["timeout"]:
            raise RuntimeError(f"synthetic build failed; see {result / 'build.process.json'}")
        binary = result / "OLMBlur.aex"
        shutil.copy2(target / "release" / "triage_synthetic_blur.dll", binary)
        builds.append(t.oracle.identity(binary))
    provenance = {"builds": builds, "source_changes": "triage_legacy_amount multiplier: 2.0f32 -> 3.0f32",
                  "expected_parameter": "Legacy", "expected_function": "triage_legacy_amount",
                  "production_source_hashes": {str(p.relative_to(source)): t.oracle.sha256(p) for p in source.rglob("*.rs")}}
    t.oracle.write_json(out / "builds.json", provenance)
    return provenance


def verify(path):
    report = json.loads(path.read_text(encoding="utf-8"))
    changed = report["binary_diff"]["changed"]
    assert any("triage_legacy_amount" in p["new"]["name"] for p in changed), "changed helper not localized"
    code_changes = [p["new"]["name"] for p in changed if p.get("change_kind") == "instructions"]
    assert code_changes == ["triage_legacy_amount"], code_changes
    affected = [p["name"] for p in report["parameter_sensitivity"] if p["mismatched"]]
    assert affected == ["Legacy"], affected
    assert not report["inventory_diff"] and not report["pipl_diff"]
    assert not report["incomplete"]
    assert all(r["status"] == "exact" for r in report["sensitivity"]["cases"] if r.get("label") == "defaults")
    print("PASS: helper localized; only Legacy exposes change; defaults, inventory and PiPL equal")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path)
    p.add_argument("--verify", type=Path)
    args = p.parse_args()
    if args.verify:
        verify(args.verify)
    elif args.out:
        build_pair(args.out.resolve())
    else:
        p.error("specify --out or --verify")
