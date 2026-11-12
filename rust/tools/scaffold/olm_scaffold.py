#!/usr/bin/env python3
"""Generate a Windows AE CPU scaffold from measured AEX declarations (no algorithm port)."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ORACLE = HERE.parent / "oracle" / "olm_oracle.py"
REV = "0e0b197850f28c1bb24e8c82fce2e3d4c120d1e9"
DEFAULT_HARNESS = Path(r"D:\Projects\01_Project\04_Tools\AEXCompat-wt-main\broker\target\release\aexcompat-harness.exe")
TYPE_NAMES = {0:"layer", 1:"slider", 2:"fixed_slider", 3:"angle", 4:"checkbox", 5:"color",
              6:"point", 7:"popup", 10:"float_slider", 11:"arbitrary_data", 13:"group_start", 14:"group_end"}
RESERVED = set("as async await break const continue crate dyn else enum extern false fn for if impl in let loop match mod move mut pub ref return self static struct super trait true type union unsafe use where while abstract become box do final macro override priv typeof unsized virtual yield try gen lib test std core alloc proc_macro".split())


def oracle_module():
    spec = importlib.util.spec_from_file_location("scaffold_oracle", ORACLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def pipl_properties(data):
    """Windows PiPL: two-byte resource marker, version/count, aligned properties."""
    if len(data) < 10 or data[:6] != b"\x01\0\0\0\0\0":
        raise ValueError("unsupported Windows PiPL header")
    count = struct.unpack_from("<I", data, 6)[0]
    at, result = 10, {}
    for _ in range(count):
        if at+16 > len(data):
            raise ValueError("truncated PiPL property")
        vendor, key, ident, size = struct.unpack_from("<4s4sII", data, at)
        end = at+16+size
        if end > len(data) or vendor != b"MIB8" or ident != 0:
            raise ValueError("unsupported/truncated PiPL property")
        name = key[::-1].decode("ascii")
        if name in result:
            raise ValueError(f"duplicate PiPL property: {name}")
        result[name] = data[at+16:end]
        at += 16+(size+3)//4*4
    if at != len(data):
        raise ValueError("PiPL trailing bytes or missing padding")
    return result


def resources(path):
    import pefile
    with pefile.PE(str(path), fast_load=True) as pe:
        if pe.FILE_HEADER.Machine != 0x8664:
            raise ValueError("only Windows x64 AEX is supported")
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
        result = []
        directory = getattr(pe, "DIRECTORY_ENTRY_RESOURCE", None)
        for typ in directory.entries if directory else ():
            if str(typ.name).upper() != "PIPL":
                continue
            for name in typ.directory.entries:
                for lang in name.directory.entries:
                    d = lang.data.struct
                    data = pe.get_data(d.OffsetToData, d.Size)
                    if len(data) != d.Size:
                        raise ValueError("truncated resource")
                    result.append({"name": str(name.name) if name.name else name.id,
                                   "language": lang.id, "type": str(typ.name), "bytes": data})
        if not result:
            raise ValueError("no PiPL resources")
        if len({r['bytes'] for r in result}) != 1:
            raise ValueError("multiple distinct PiPL effects are not supported")
        return result


def descriptor(res):
    p = pipl_properties(res[0]["bytes"])
    def pascal(key):
        b = p[key]
        if not b or b[0]+1 > len(b):
            raise ValueError(f"invalid PiPL string {key}")
        return b[1:1+b[0]].decode("utf-8", errors="backslashreplace")
    if p.get("kind") != b"TKFe":
        raise ValueError("PiPL is not an AE effect")
    entry = p["8664"].split(b"\0", 1)[0].decode("ascii")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", entry):
        raise ValueError("unsupported entry symbol")
    return {"name": pascal("name"), "match_name": pascal("eMNA"), "category": pascal("catg"),
            "entry": entry, "version": struct.unpack("<I", p["eVER"])[0],
            "flags": struct.unpack("<I", p["eGLO"])[0], "flags2": struct.unpack("<I", p["eGL2"])[0]}


def run_checked(oracle, argv, timeout, env=None, log=None):
    r = oracle.run_process(argv, timeout, env)
    if log:
        write_json(log, r)
    if r["returncode"] or r["timeout"] or r["cancelled"]:
        raise RuntimeError(f"command failed: {argv[0]} (exit {r['returncode']}); {r['stderr'][-3000:]}")
    return r


def build_probe(oracle, directory):
    target = directory / "target"
    run_checked(oracle, ["cargo", "build", "--offline", "--locked", "--manifest-path", HERE/"probe/Cargo.toml",
                        "--target-dir", target, "-j", "2"], 600, log=directory/"probe-build.json")
    probe = directory / "capture.aex"
    shutil.copy2(target/"debug/olm_scaffold_probe.dll", probe)
    return probe


def validate_capture(inv, capture):
    if capture.get("schema_version") != 1:
        raise ValueError("unsupported capture schema")
    params = capture["params"]
    if len(params)+1 != inv["host"]["reported_num_params"] or len(params) != len(inv["parameters"]):
        raise ValueError("capture and inventory parameter counts differ")
    if capture["num_params"] != len(params)+1:
        raise ValueError("non-contiguous parameter setup unsupported")
    metadata = {p["index"]: p for p in inv["host"]["parameter_metadata"]}
    for n, (a, b) in enumerate(zip(params, inv["parameters"]), 1):
        if a["slot"] != n or b["slot"] != n or a["add_index"] not in (-1, n):
            raise ValueError("non-contiguous parameter slot order")
        if not a["supported"] or TYPE_NAMES.get(a["fields"]["param_type"]) != metadata[n]["type"]:
            raise ValueError(f"unhandled or inconsistent parameter type at slot {n}")
        if a.get("arbitrary") and (a["arbitrary"]["size_error"] or a["arbitrary"]["flatten_error"]):
            raise ValueError(f"cannot capture arbitrary default at slot {n}; manual implementation required")
        if a.get("arbitrary") and any(type(v) is not int or not 0 <= v <= 255 for v in a["arbitrary"]["default_flat"]):
            raise ValueError(f"invalid flattened byte array at slot {n}")
    for key in ("flags", "flags2"):
        if capture[key] != inv["host"]["advertised_out_"+key]:
            raise ValueError("runtime flags differ between capture and inventory")


def rust_value(value):
    if isinstance(value, dict):
        for typ in ("f32", "f64"):
            if set(value) == {typ+"_bits"}:
                return f"{typ}::from_bits({int(value[typ+'_bits'])})"
        raise ValueError("invalid numeric bit representation")
    if type(value) is not int:
        raise ValueError("expected integer field")
    return str(value)


def field_path(path):
    if not re.fullmatch(r"(?:uu\.id|u\.cd\.(?:value|dephault)\.(?:alpha|red|green|blue)|(?:u\.[a-z_]+\.)?[A-Za-z_][A-Za-z_0-9]*)", path):
        raise ValueError(f"invalid Rust field path: {path}")
    return "p."+path


def params_source(inv, capture):
    lines = ["//! Measured original PARAMS_SETUP, cross-checked with AEXCompat inventory.",
             "//! Slot order, disk IDs and raw numeric bits are intentional; do not normalize.",
             "use after_effects_sys::*;", "use crate::ae::{Result, BAD, check};"]
    for key in ("version", "flags", "flags2"):
        lines.append(f"pub const {key.upper()}: u32 = {capture[key]};")
    defaults = {}
    for p in capture["params"]:
        if "arbitrary" in p:
            ident = p["fields"]["u.arb_d.id"]
            data = p["arbitrary"]["default_flat"]
            if ident in defaults and defaults[ident] != data:
                raise ValueError("ambiguous arbitrary ID defaults")
            defaults[ident] = data
    lines += ["pub fn arbitrary_default(id:i16)->Option<&'static [u8]> { match id {"]
    for ident, data in defaults.items():
        lines.append(f"{ident} => Some(&{data}),")
    lines += ["_=>None }}", "pub unsafe fn setup(i:&PF_InData,o:&mut PF_OutData)->Result<()> {",
              "let add=i.inter.add_param.ok_or(BAD)?;"]
    for p, public in zip(capture["params"], inv["parameters"]):
        name = public["name"].replace("\n", " ").replace("\r", " ")
        lines += [f"// Slot {p['slot']}: {name}; {TYPE_NAMES[p['fields']['param_type']]}",
                  "{ let mut p:PF_ParamDef=std::mem::zeroed();"]
        for k, v in p["fields"].items():
            lines.append(f"{field_path(k)} = {rust_value(v)};")
        lines.append(f"p.name = {p['name']};")
        for k, array in p["arrays"]:
            lines.append(f"{field_path(k)} = {array};")
        if p["label"]:
            k, label = p["label"]
            if k not in ("u.bd.u.nameptr", "u.pd.u.namesptr"):
                raise ValueError("unsupported label")
            lines.append(f"const LABEL: &[u8] = &{label+[0]}; p.{k} = LABEL.as_ptr().cast();")
        if "arbitrary" in p:
            ident = p["fields"]["u.arb_d.id"]
            lines += [f"p.u.arb_d.dephault = crate::arbitrary::new(i,arbitrary_default({ident}).ok_or(BAD)?)?;",
                      f"let error=add(i.effect_ref,{p['add_index']},&mut p);",
                      "if error!=0 {crate::arbitrary::dispose(i,p.u.arb_d.dephault)?;} check(error)?;"]
        else:
            lines.append(f"check(add(i.effect_ref,{p['add_index']},&mut p))?;")
        lines.append("}")
    if capture["custom_ui_events"]:
        lines += ["let mut ui:PF_CustomUIInfo=std::mem::zeroed();",
                  f"ui.events={capture['custom_ui_events']};",
                  "check(i.inter.register_ui.ok_or(BAD)?(i.effect_ref,&mut ui))?;"]
    lines += [f"o.num_params={capture['num_params']}; Ok(())", "}"]
    return "\n".join(lines)+"\n"


def limitations(inv, capture):
    return {"algorithm": "TODO: byte-copy stub only; no original render equivalence",
            "dynamic_ui": "TODO: state transitions cannot be inferred from PARAMS_SETUP/inventory",
            "custom_ui_events": capture["custom_ui_events"],
            "supervised_slots": [p["slot"] for p in inv["parameters"] if p["supervised"]],
            "arbitrary_slots": [p["slot"] for p in capture["params"] if "arbitrary" in p],
            "arbitrary_semantics": "Opaque flatten/unflatten/copy only; unknown bytes preserved verbatim; no interior interpolation, print/scan or editor. Captured defaults may include unstable inactive bytes.",
            "host_behavior": "TODO: original ROI expansion, temporal inputs, secondary-layer use, sequence/global state, audio/GPU and dynamic flags are not reconstructed",
            "platforms": "Windows x64 CPU scaffold; native AE and macOS bundle/PiPL/entry generation unverified"}


def emit(out, name, aex, inv, cap, res, desc, harness):
    validate_capture(inv, cap)
    source = params_source(inv, cap)
    if inv["host"].get("audio_effect_only") or not inv["host"].get("image_render_supported"):
        raise ValueError("only CPU image effects supported")
    if inv["host"].get("plugin_data") is not None:
        raise ValueError("PluginDataEntryFunction registration requires manual generation")
    out.mkdir(parents=True, exist_ok=False)
    (out/"src").mkdir(); (out/"resources").mkdir(); (out/"tests").mkdir()
    (out/"Cargo.toml").write_text(f'''[package]
name = {json.dumps(name)}
version = "0.1.0"
edition = "2021"
publish = false
[workspace]
[lib]
crate-type = ["cdylib", "rlib"]
[target.'cfg(windows)'.dependencies]
after-effects-sys = {{ git = "https://github.com/virtualritz/after-effects.git", rev = "{REV}" }}
[build-dependencies]
winres = "=0.1.12"
''', encoding="utf-8")
    rc = []
    for n, r in enumerate(res):
        file = f"resources/pipl-{n}.bin"
        (out/file).write_bytes(r["bytes"])
        ident = str(r["name"]) if isinstance(r["name"], int) else json.dumps(r["name"])
        language = r["language"]
        rc.append(f'LANGUAGE {language & 0x3ff}, {language >> 10}\n{ident} {r["type"]} DISCARDABLE "{file}"')
    (out/"build.rs").write_text('''// Raw resources avoid the code-page-sensitive PiPL string serializer.
fn main() {
    println!("cargo:rerun-if-changed=resources");
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref()==Ok("windows") {
        winres::WindowsResource::new().append_rc_content(RC).compile().unwrap();
    }
}
const RC:&str = '''+json.dumps("\n".join(rc))+";\n", encoding="utf-8")
    for file in ("algorithm.rs", "ae.rs", "arbitrary.rs", "arbitrary_tests.rs", "ui.rs"):
        shutil.copy2(HERE/"templates"/file, out/"src"/file)
    (out/"src/params.rs").write_text(source, encoding="utf-8")
    (out/"src/lib.rs").write_text('pub mod algorithm;\n'+''.join(f'#[cfg(windows)]\nmod {m};\n' for m in ("params", "ae", "arbitrary", "ui")), encoding="utf-8")
    if desc["entry"] != "EffectMain":
        with (out/"src/ae.rs").open("a", encoding="utf-8") as f:
            f.write(f'''\n#[export_name = {json.dumps(desc['entry'])}]
pub unsafe extern "C" fn original_entry_alias(cmd:PF_Cmd,i:*mut PF_InData,o:*mut PF_OutData,p:PF_ParamList,w:*mut PF_LayerDef,e:*mut c_void)->PF_Err {{entry(cmd,i,o,p,w,e)}}
''')
    routes = [r for r in ("smart8", "smart16", "smart32", "classic8", "classic16")
              if oracle_module().route_support(inv, r) is None]
    config = {"schema_version":1, "reference":str(aex), "candidate":f"target/release/{name.replace('-', '_')}.dll",
              "harness":str(harness), "oracle":str(ORACLE), "routes":routes, "jobs":1,
              "cases":12, "seed":20261112, "downsample":"1,1/2,1/4", "expect_render_match":False}
    write_json(out/"oracle.json", config)
    write_json(out/"inventory.json", inv)
    write_json(out/"declarations.json", cap)
    write_json(out/"scaffold.json", {"schema_version":1,"original":{"path":str(aex),"sha256":sha(aex.read_bytes())},
                "descriptor":desc,"resources":[{k:v for k,v in r.items() if k!="bytes"}|{"sha256":sha(r["bytes"])} for r in res],
                "limitations":limitations(inv,cap),"generator_sha256":sha(Path(__file__).read_bytes())})
    (out/".gitignore").write_text("target/\nlocal/\n*.aex\n", encoding="utf-8")
    for template in ("reference.rs", "passthrough.rs"):
        text = (HERE/"templates"/template).read_text(encoding="utf-8").replace("CRATE_IDENT", name.replace("-", "_"))
        (out/"tests"/template).write_text(text, encoding="utf-8")
    shutil.copy2(HERE/"templates/verify_reference.py", out/"verify_reference.py")
    (out/"VALIDATION.md").write_text(f'''# {desc['name']} scaffold validation

Status: **ALGORITHM NOT PORTED**. Rendering is byte-for-byte input copying.
Inventory equality is declaration evidence, not render or saved-project compatibility.

- Original SHA-256: `{sha(aex.read_bytes())}`
- Declared normal CPU routes: {', '.join(routes)}
- Exact original Windows PiPL is under `resources/`; entry alias: `{desc['entry']}`.
- `inventory.json`: original AEXCompat inspection. `declarations.json`: supplemental
  PARAMS_SETUP capture for disk IDs, flags, initial values, precision and raw strings.
- `scaffold.json`: provenance, PiPL resource hashes and per-plugin TODO inventory.

## Required evidence (fill in after implementing)

| Check | Result | Evidence / hashes |
| --- | --- | --- |
| cargo build --release | TODO | |
| cargo test | TODO | |
| python verify_reference.py inventory --out local/inventory | TODO | |
| Full PiPL resource bytes / IDs / languages | TODO | |
| Original render oracle, each route/depth/scale | NOT EXPECTED TO MATCH STUB | |
| Parameter edits, dynamic UI and custom controls | TODO | |
| Arbitrary flatten/unflatten and saved-project round trip | TODO | |
| Native AE acceptance | NOT RUN | |
| macOS bundle and host acceptance | NOT IMPLEMENTED | |

## Manual work

Replace `src/algorithm.rs`, introduce owned parameter snapshots/checkouts and port
original ROI/temporal/secondary-layer behavior. The current stub ignores controls.
`src/ui.rs` deliberately does not invent conditional UI or custom drawing behavior.
Custom UI event mask: {cap['custom_ui_events']}; arbitrary slots:
{limitations(inv,cap)['arbitrary_slots']}. Opaque data retains unknown flattened
bytes through copy and save/load; semantic equality/interpolation, print/scan,
and editor behavior require a port. Interior interpolation fails explicitly.
Captured defaults can contain unstable inactive original bytes: do not infer their
meaning or normalize them. Runtime global flags may differ from PiPL; both are retained.
Original flags can advertise capabilities the TODO stub does not implement.
Do not install/distribute this scaffold as a replacement for the original.
''', encoding="utf-8")


def new(args):
    if os.name != "nt":
        raise ValueError("capture requires Windows x64 and AEXCompat")
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*", args.crate_name) or args.crate_name.replace('-', '_') in RESERVED:
        raise ValueError("crate name must be a non-keyword lowercase Cargo identifier")
    aex = args.aex.resolve(strict=True); out = args.out.resolve()
    if out.exists():
        raise ValueError("output already exists; choose a new directory")
    if (HERE.parents[1]/"plugins") in out.parents or out == HERE.parents[1]/"plugins":
        raise ValueError("generate outside rust/plugins; move manually after review")
    res = resources(aex); desc = descriptor(res)
    oracle = oracle_module()
    local = HERE/"local"; local.mkdir(exist_ok=True)
    # Retained ignored evidence, not a daemon or installed plug-in.
    work = Path(tempfile.mkdtemp(prefix="capture-", dir=local))
    probe = args.probe.resolve(strict=True) if args.probe else build_probe(oracle, work)
    print(f"Inspecting {aex.name}; evidence: {work}", flush=True)
    inv = oracle.inspect(args.harness.resolve(), aex, args.timeout)
    write_json(work/"inventory.json", inv)
    env = {"OLM_SCAFFOLD_ORIGINAL":str(aex), "OLM_SCAFFOLD_ENTRY":desc["entry"],
           "OLM_SCAFFOLD_CAPTURE":str(work/"declarations.json")}
    run_checked(oracle, [args.harness.resolve(), "--headless", "--inspect-experimental-with-deps", probe, aex.parent],
                args.timeout, env, work/"capture-run.json")
    cap = json.loads((work/"declarations.json").read_text(encoding="utf-8"))
    emit(out, args.crate_name, aex, inv, cap, res, desc, args.harness.resolve())
    print(f"Generated {out}: {len(cap['params'])} params; exact PiPL; algorithm/UI TODO", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("new")
    p.add_argument("--aex", required=True, type=Path)
    p.add_argument("--crate-name", required=True)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--harness", type=Path, default=DEFAULT_HARNESS)
    p.add_argument("--timeout", type=float, default=60)
    p.add_argument("--probe", type=Path, help="reuse a built capture.aex; otherwise build the bundled proxy offline")
    args = parser.parse_args(argv)
    try:
        new(args)
    except (ValueError, RuntimeError, OSError, KeyError) as e:
        print(f"scaffold: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
