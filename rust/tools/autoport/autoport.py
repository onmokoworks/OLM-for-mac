#!/usr/bin/env python3
"""Resumeable, bounded Ghidra -> Codex -> native witness -> render-oracle loop."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import time

from process import codex_executable, run, witness_module
from vectors import generate, pack

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
ROOT = HERE.parents[2]
SUCCESS = {"verified", "known_verified"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    os.replace(temp, path)


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def hub(url):
    spec = importlib.util.spec_from_file_location("autoport_hub", TOOLS/"ghidra-hub/client.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Client(url, timeout=180)


def leaf_order(nodes, edges):
    """Kahn ordering leaves first. Cycles and their dependent ancestors stay blocked."""
    remaining = set(nodes)
    deps = {n:{b for a,b in edges if a == n and b in nodes} for n in nodes}
    order = []
    while remaining:
        leaves = sorted(n for n in remaining if not deps[n] & remaining)
        if not leaves:
            break
        order.extend(leaves)
        remaining.difference_update(leaves)
    return order, sorted(remaining)


def clean_c(source):
    # Hub comments can contain links or excerpts of already ported algorithms.
    # Strip those comments, retain an unmodified original export for the auditor.
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S).strip()


def infer_scalar_contract(node):
    """Conservative optional inference. Unknown-width types and pointers stop here.

    This is a witness admission heuristic, not proof that Ghidra recovered the ABI.
    Demo contracts remain explicit and hash-bound to their exported original.
    """
    if not node.get("c"):
        return None
    code = clean_c(node["c"])
    types = {"int":"i32","uint":"u32","short":"i16","ushort":"u16",
             "char":"i8","byte":"u8","longlong":"i64","ulonglong":"u64",
             "float":"f32","double":"f64"}
    match = re.match(r"(\w+)\s+(?:__\w+\s+)?\w+\s*\(([^)]*)\)\s*\{",code)
    if not match or match[1] not in types:
        return None
    if re.search(r"\b(?:DAT_|PTR_|in_|unaff_|uRam|iRam)|\b(?:undefined\w*|code)\b|->|\[|\*\s*\)",code):
        return None
    args = []
    for parameter in ([] if match[2].strip() in {"","void"} else match[2].split(",")):
        p = parameter.strip().split()
        if len(p) != 2 or p[0] not in types or not re.fullmatch(r"\w+",p[1]):
            return None
        args.append((p[1],types[p[0]]))
    name = f"autoport_{node['address']}"
    return {"fixture":"scalar","abi":{"args":[t for _,t in args],"return":types[match[1]]},
            "rust_signature":f'pub unsafe extern "C" fn {name}('+", ".join(f"{n}: {t}" for n,t in args)+f") -> {types[match[1]]}",
            "notes":"Conservatively inferred scalar-only Ghidra ABI. No pointers or recovered global-state artifacts admitted. Native witness remains mandatory."}


def export(config, out):
    import pefile
    client = hub(config["hub"])
    identity = next(p for p in client.programs_list() if p["name"] == config["program"])
    if identity["sha256"].lower() != digest(config["aex"]):
        raise ValueError("hub program and original binary hashes differ")
    nodes, edges, pending = {}, set(), list(config["roots"])
    cap = config["max_nodes"]
    while pending and len(nodes) < cap:
        batch = pending[:min(32, cap-len(nodes))]
        pending = pending[len(batch):]
        graph = client.call_graph(program=config["program"], functions=batch, depth=0)
        nodes.update((n["address"], n) for n in graph["nodes"])
        edges.update(tuple(e) for e in graph["edges"])
        pending = sorted((set(pending) | {b for _,b in edges}) - set(nodes))
        # External imports cannot be selected as internal functions by the API.
        for a in list(pending):
            if a.startswith("EXTERNAL:") and len(nodes) < cap:
                nodes[a] = {"address":a,"name":a,"external":True}
                pending.remove(a)
    # Keep missing endpoints visible, never silently certify a depth-truncated graph.
    frontier = sorted({b for _,b in edges}-set(nodes))
    internal = [n for n in nodes.values() if not n.get("external")]
    for start in range(0, len(internal), 16):
        result = client.decompile_batch(items=[{"program":config["program"],"function":n["address"]}
            for n in internal[start:start+16]], parallel=False, timeout=30)
        for row in result["results"]:
            address = row.get("address", row.get("function"))
            nodes[address].update(row)
            if row.get("c"):
                p = out/"exports"/f"{address}.c"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(row["c"], encoding="utf-8")
    with pefile.PE(config["aex"], fast_load=False) as pe:
        imports = [{"kind":kind,"dll":d.dll.decode(errors="replace"),
                    "name":i.name.decode(errors="replace") if i.name else f"#{i.ordinal}"}
                   for kind,table in [("normal","DIRECTORY_ENTRY_IMPORT"),("delay","DIRECTORY_ENTRY_DELAY_IMPORT")]
                   for d in getattr(pe,table,[]) for i in d.imports]
        base = pe.OPTIONAL_HEADER.ImageBase
    data = {"identity":identity,"image_base":base,"nodes":nodes,"edges":sorted(edges),
            "frontier":frontier,"imports":imports,"indirect_calls":"not resolved exhaustively",
            "root_evidence":config.get("root_evidence", "user supplied roots")}
    write(out/"graph.json", data)
    return data


def progress(out, state):
    write(out/"state.json", state)
    lines = ["# Automatic port progress", "", f"Status: {state.get('status','in_progress')}", "",
             "| Function | Status | Attempts | Seconds | Reason |", "|---|---|---:|---:|---|"]
    for address, row in state["functions"].items():
        reason = row.get("reason", "").replace("|", "/").replace("\n", " ")[:220]
        lines.append(f"| {address} | {row['status']} | {len(row['attempts'])} | {row.get('seconds',0):.3f} | {reason} |")
    (out/"progress.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


def prompt_for(node, contract, signatures, imports, fma, feedback=None):
    export_name = f"autoport_{node['address']}"
    return f'''Translate exactly ONE original Windows x64 function to portable Rust 2021.
Return JSON only with keys code (complete Rust source), notes (short string).
Use no tools, no filesystem reads, no external integrations. All input is below.
Do not read any existing Rust plug-in translation, C++ port, or expected-result table.
The controller writes your returned source into a scaffold crate and runs witness.
Emit #[no_mangle] pub unsafe extern "C" fn {export_name} with this exact ABI:
{contract['rust_signature']}
Do not include modules/files, build scripts, tests, main, foreign linking, process/IO,
inline assembly, external original DLL calls, or per-test expected-value substitutions.
Private helpers are allowed. Callee imports must use crate::autoport::<export_name>.
Preserve original operation order, widths, signedness, casts and sequential stores,
including pointer alias behavior. Do not simplify or reassociate arithmetic.
Use olm_math UCRT transcendental calls, never std f32/f64 transcendental methods.
UCRT lane is olm_math::Mode::{'Fma' if fma == 'fma' else 'NoFma'} ({fma}).
Never use mul_add unless the original explicitly fused that operation. For x86
CVTTSS2SI use olm_math::x86::cvttss2si (Rust casts saturate differently).
Preserve NaN payloads, signed zero, gradual underflow and operation precision.
ABI/domain notes (reviewed input, not a translated algorithm):
{contract.get('notes','')}
Already verified callees and their Rust signatures:
{json.dumps(signatures, indent=2)}
Original module imports (not an authorization to call the original):
{json.dumps(imports)}
Ghidra stored signature: {node.get('signature')}
Ghidra C (stored types may be stale; the reviewed ABI above takes precedence):
```c
{clean_c(node['c'])}
```
Previous failure, if any (fix semantics, never special-case these vectors):
{json.dumps(feedback, indent=2) if feedback else 'none'}
'''


def validate_source(code, name):
    if not re.search(r'pub\s+unsafe\s+extern\s+"C"\s+fn\s+'+re.escape(name)+r'\s*\(', code):
        raise ValueError("missing required exported ABI function")
    if re.search(r'include(?:_bytes|_str)?!?\s*\(|#\s*\[\s*(?:path|link)|\b(?:asm|global_asm)!|std::(?:fs|process|net)|\bextern\s+"[^\"]+"\s*\{', code):
        raise ValueError("source contains forbidden external execution/embedding")
    if re.search(r'\.(?:sin|cos|exp|exp2|ln|log|log2|log10|powf|powi|atan|atan2|tan)\s*\(', code):
        raise ValueError("std transcendental prohibited; use olm_math")


def write_modules(work, state, current=None):
    directory = work/"src/autoport"
    directory.mkdir(exist_ok=True)
    names = [a for a,r in state["functions"].items() if r["status"] in SUCCESS]
    if current and current not in names:
        names.append(current)
    (directory/"mod.rs").write_text("\n".join(f"mod f_{a};\npub use f_{a}::*;" for a in sorted(names))+"\n", encoding="utf-8")


def exported_rva(dll, name):
    import pefile
    with pefile.PE(str(dll)) as pe:
        found = [e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name == name.encode()]
    if len(found) != 1:
        raise ValueError(f"missing or ambiguous Rust export {name}")
    return found[0]


def compare_witness(original, candidate, spec):
    a, b = read(original/"result.json"), read(candidate/"result.json")
    if len(a["calls"]) != len(spec["calls"]) or len(b["calls"]) != len(a["calls"]):
        raise ValueError("incomplete witness call count")
    pointer_offsets = [p["offset"] for p in spec.get("buffers",{}).get("arena",{}).get("pointers",[])]
    for i, (x,y) in enumerate(zip(a["calls"], b["calls"])):
        if x["index"] != i or y["index"] != i:
            raise ValueError("witness call ordering changed")
        if x["return"]["bits_le"] != y["return"]["bits_le"]:
            return {"index":i,"kind":"return","expected":x["return"]["bits_le"],"actual":y["return"]["bits_le"]}
        if set(x["buffers"]) != set(spec.get("buffers",{})) or set(y["buffers"]) != set(x["buffers"]):
            raise ValueError("incomplete witness buffers")
        for name in x["buffers"]:
            left = bytearray((original/x["buffers"][name]).read_bytes())
            right = bytearray((candidate/y["buffers"][name]).read_bytes())
            if len(left) != spec["buffers"][name]["size"] or len(right) != len(left):
                raise ValueError("witness buffer size differs")
            if pointer_offsets:
                anchor = pointer_offsets[-1]
                for data in [left,right]:
                    base = int.from_bytes(data[anchor:anchor+8],"little")
                    if not base:
                        raise ValueError("witness relocation anchor corrupted")
                    for offset in pointer_offsets:
                        value = int.from_bytes(data[offset:offset+8],"little")
                        normalized = ((value-base) & ((1<<64)-1)) if value else (1<<64)-1
                        data[offset:offset+8] = normalized.to_bytes(8,"little")
            if left != right:
                offset = next(j for j,(l,r) in enumerate(zip(left,right)) if l != r)
                return {"index":i,"kind":"buffer","offset":offset,
                        "expected":left[max(0,offset-8):offset+16].hex(),
                        "actual":right[max(0,offset-8):offset+16].hex()}
    return None


def verify(contract, rows, config, address, graph, dll, attempt, deadline):
    w = witness_module()
    rva = int(address,16)-graph["image_base"]
    candidate_rva = exported_rva(dll, f"autoport_{address}")
    spec = pack(rows, config["aex"], rva, config["fma"])
    manifests = []
    for side, module, offset in [("original",config["aex"],rva),("rust",dll,candidate_rva)]:
        submitted = copy.deepcopy(spec)
        submitted["module"] = str(module)
        for call in submitted["calls"]:
            call["rva"] = hex(offset)
        timeout = min(config["witness_seconds"], deadline-time.monotonic())
        if timeout <= 0:
            raise TimeoutError("function budget exhausted before witness")
        manifest = w.run(submitted, attempt/side, timeout=timeout)
        manifests.append(manifest)
        if manifest["classification"] != "success" or not manifest["process"]["cleanup_verified"]:
            raise RuntimeError(f"{side} witness {manifest['classification']}; not a translation mismatch")
        if side == "original" and manifest["module_sha256"] != graph["identity"]["sha256"].lower():
            raise ValueError("original binary changed since hub export")
        profile = read(attempt/side/"result.json")["fma"]
        if profile["effective"] != (1 if config["fma"] == "fma" else 0):
            raise ValueError("native UCRT did not select the requested FMA lane")
        if int(profile["mxcsr"],16) & (0x8000 | 0x6000 | 0x40):
            raise ValueError("witness requires round-to-nearest and gradual underflow")
    # On math functions this controls the system UCRT; embedded/private CRTs need a contract.
    failure = compare_witness(attempt/"original", attempt/"rust", spec)
    result = {"vectors":len(rows),"exact":failure is None,"failure":failure,
              "original_sha256":manifests[0]["module_sha256"], "candidate_sha256":manifests[1]["module_sha256"]}
    if failure:
        # One independently initialized call is a minimal failing *case*, not a
        # claim of value-wise shrinking. Keep the full failing input in feedback.
        index = failure["index"]
        minimal = rows[index]
        result["minimal_vector"] = minimal
        for side, module, offset in [("minimal-original",config["aex"],rva),("minimal-rust",dll,candidate_rva)]:
            time_left = min(config["witness_seconds"], deadline-time.monotonic())
            if time_left <= 0:
                result["minimal_reproduced"] = False
                break
            m = w.run(pack([minimal],module,offset,config["fma"]), attempt/side, timeout=time_left)
            if m["classification"] != "success":
                result["minimal_reproduced"] = False
                break
        else:
            mini_spec = pack([minimal],config["aex"],rva,config["fma"])
            result["minimal_reproduced"] = compare_witness(attempt/"minimal-original",attempt/"minimal-rust",mini_spec) is not None
    write(attempt/"comparison.json", result)
    if failure and not result.get("minimal_reproduced"):
        raise RuntimeError("minimal call did not independently reproduce; review shared native state/sequence ABI")
    return result


def known_lookup(config, graph):
    """Optional hash-bound exchange file, never accept a name/shape match as verified."""
    path = config.get("known_functions")
    if not path:
        return {}, "funcdb absent or no verified exchange supplied; skipped"
    table = read(path)
    found = {}
    for item in table["functions"]:
        if (item.get("verified") is True and item.get("original_sha256") == graph["identity"]["sha256"]
            and item.get("evidence") and item["address"] in graph["nodes"]):
            source = (Path(path).parent/item["rust_source"]).resolve(strict=True)
            if digest(source) != item["rust_sha256"]:
                raise ValueError("known Rust function source hash differs")
            evidence = (Path(path).parent/item["evidence"]).resolve(strict=True)
            if digest(evidence) != item["evidence_sha256"]:
                raise ValueError("known function evidence hash differs")
            found[item["address"]] = {**item,"rust_source":str(source)}
    return found, f"{len(found)} hash-bound verified functions admitted"


def setup_work(config, out):
    work = out/"work"
    def stage_dir(name):
        number = 1
        while (out/"setup"/f"{name}-{number}").exists():
            number += 1
        return out/"setup"/f"{name}-{number}"
    # Build the public scaffold capture proxy in our owned directory.
    probe = out/"probe-target/debug/olm_scaffold_probe.dll"
    command = ["cargo","build","--offline","--locked","--manifest-path",TOOLS/"scaffold/probe/Cargo.toml",
               "--target-dir",out/"probe-target","-j","2"]
    if not work.exists():
        build = run(command,stage_dir("probe"),config["setup_seconds"])
        if build["returncode"] or build["timeout"]:
            raise RuntimeError("scaffold proxy build failed")
        staged = out/"capture.aex"
        shutil.copyfile(probe,staged)  # break Cargo hardlinks, required by AEXCompat
        log = stage_dir("scaffold")
        candidate = log/"candidate"
        argv = [sys.executable,HERE/"adapters.py",config["aex"],candidate,config["crate_name"],staged,log/"evidence"]
        result = run(argv,log,config["setup_seconds"])
        if result["returncode"] or result["timeout"]:
            raise RuntimeError("scaffold generation failed")
        if not candidate.resolve().is_relative_to(out.resolve()) or not work.resolve().is_relative_to(out.resolve()):
            raise ValueError("scaffold publication escaped the owned run")
        candidate.rename(work)  # completed scaffold only; interrupted staging is retained
    if not (work/"scaffold.json").exists() or not (work/"src/lib.rs").exists():
        raise ValueError("interrupted partial scaffold; inspect it and use a fresh output directory")
    cargo = work/"Cargo.toml"
    if 'olm-math = ' not in cargo.read_text(encoding="utf-8"):
        with cargo.open("a",encoding="utf-8") as f:
            f.write('\n[dependencies]\nolm-math = { path = '+json.dumps((ROOT/"rust/crates/olm-math").as_posix())+' }\n')
    lib = work/"src/lib.rs"
    if "pub mod autoport;" not in lib.read_text(encoding="utf-8"):
        with lib.open("a",encoding="utf-8") as f:
            f.write("\npub mod autoport;\n")
    (work/"src/autoport").mkdir(exist_ok=True)
    if not (work/"src/autoport/mod.rs").exists():
        (work/"src/autoport/mod.rs").write_text("",encoding="utf-8")
    result = run(["cargo","build","--release","--offline","--manifest-path",work/"Cargo.toml","-j","2"],
                 stage_dir("build"),config["setup_seconds"],env={"CARGO_TARGET_DIR":str(work/"target")})
    if result["returncode"] or result["timeout"]:
        raise RuntimeError("initial work crate build failed")


def annotate(config, graph, state, out):
    rows = []
    client = hub(config["hub"])
    for a,r in state["functions"].items():
        if r["status"] not in SUCCESS:
            continue
        # Refresh the current comment immediately before merging; no rename API.
        fresh = client.call_graph(program=config["program"],functions=[a],depth=0)["nodes"][0]
        marker = f"[L-autoport {state['run_id']} {a}]"
        if marker in fresh.get("comment", ""):
            continue
        message = f"{marker} Rust autoport_{a}; status={r['status']}; bounded corpus only; evidence={out/'state.json'}; source_sha256={r['source_sha256']}"
        rows.append({"program":config["program"],"function":a,
                     "expected_name":fresh["name"],"comment":fresh.get("comment","")+"\n"+message})
    if rows:
        write(out/"annotations.json",client.bulk_edit(rows=rows,provenance="Job L-autoport: bounded witness mapping; names preserved"))


def final_oracle(config, out, state, graph):
    covered = all(r["status"] in SUCCESS for a,r in state["functions"].items() if not graph["nodes"][a].get("external"))
    integration = config.get("integration")
    # Wiring is an explicitly reviewed adapter; a direct graph cannot prove that
    # host callbacks, global state, and indirect calls are covered.
    eligible = covered and not graph["frontier"] and bool(config.get("indirect_reviewed"))
    state["render_path_covered"] = eligible
    if eligible and integration:
        for target, src in integration["files"].items():
            dest = (out/"work"/target).resolve()
            if not dest.is_relative_to((out/"work/src").resolve()):
                raise ValueError("integration writes must remain under work/src")
            source = Path(src["path"]).resolve(strict=True)
            if digest(source) != src["sha256"]:
                raise ValueError("integration source identity changed")
            shutil.copyfile(source,dest)
        state["integration"] = "wired"
    else:
        state["integration"] = "blocked: render graph/ABI or reviewed host adapter incomplete"
    # Use the public check implementation with its output-root constant redirected
    # in this child only; otherwise check writes its cargo target into oracle/runs.
    driver = out/"oracle_driver.py"
    driver.write_text("import sys\nfrom pathlib import Path\n"+
        f"sys.path.insert(0,{str(TOOLS/'oracle')!r})\nimport olm_oracle, oracle_workflows\n"+
        f"oracle_workflows.HERE = Path({str(out/'oracle-owned')!r})\n"+
        "raise SystemExit(olm_oracle.main())\n",encoding="utf-8")
    oracle_out, process_out = out/"oracle", out/"oracle-process"
    retry = 1
    while oracle_out.exists() or process_out.exists():
        retry += 1
        oracle_out, process_out = out/f"oracle-{retry}",out/f"oracle-process-{retry}"
    argv = [sys.executable,driver,"check",config["crate_name"],"--rust-root",out/"work",
            "--reference",config["aex"],"--out",oracle_out,"--jobs","2","--timeout","30","--build-timeout","300"]
    p = run(argv,process_out,config["oracle_seconds"])
    state["oracle"] = {"returncode":p["returncode"],"timeout":p["timeout"],
                       "candidate_kind":"integrated" if state["integration"] == "wired" else "incomplete scaffold",
                       "evidence":str(oracle_out)}
    state["status"] = "complete" if eligible and state["integration"] == "wired" and p["returncode"] == 0 else "needs_human"


def execute(config, out):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    # A held OS file lock prevents concurrent resumes; process death releases it.
    import msvcrt
    lock = (out/"run.lock").open("a+b")
    lock.seek(0); lock.write(b"\0"); lock.flush(); lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:
        lock.close()
        raise RuntimeError("another autoport controller owns this run")
    try:
        return _execute(config,out)
    finally:
        lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1); lock.close()


def _execute(config,out):
    config_hash = fingerprint(config)
    if (out/"state.json").exists():
        state = read(out/"state.json")
        if state["config_hash"] != config_hash or state["original_sha256"] != digest(config["aex"]):
            raise ValueError("resume input/config drift; create a fresh run")
        graph = read(out/"graph.json")
        if state.get("graph_sha256") and digest(out/"graph.json") != state["graph_sha256"]:
            raise ValueError("exported graph changed since checkpoint")
    else:
        graph = export(config,out)
        setup_work(config,out)
        order, blocked = leaf_order(graph["nodes"],graph["edges"])
        state = {"schema_version":1,"run_id":out.name,"config_hash":config_hash,
                 "original_sha256":digest(config["aex"]),"graph_sha256":digest(out/"graph.json"),
                 "status":"in_progress","order":order,
                 "cycles_and_dependents":blocked,"functions":{a:{"status":"pending","attempts":[],"seconds":0}
                 for a in sorted(graph["nodes"])}}
        known, state["funcdb"] = known_lookup(config,graph)
        for a,k in known.items():
            source = Path(k["rust_source"]).read_text(encoding="utf-8")
            validate_source(source,f"autoport_{a}")
            p = out/"work/src/autoport"/f"f_{a}.rs"
            p.write_text(source,encoding="utf-8")
            state["functions"][a].update(status="known_verified",source_sha256=digest(p),rust_signature=k["rust_signature"],reason=k["evidence"])
        write(out/"config.json",config)
        progress(out,state)
    work = out/"work"
    for a,r in state["functions"].items():
        if r["status"] in SUCCESS:
            source = work/"src/autoport"/f"f_{a}.rs"
            if digest(source) != r["source_sha256"]:
                raise ValueError("verified source changed since checkpoint")
        for attempt in r["attempts"]:
            if attempt["status"] == "running":
                # Reserve full deadline on an interrupted attempt. Never restore
                # spent quota merely because the controller was interrupted.
                attempt["status"] = "interrupted"
                r["seconds"] += max(0,attempt["reserved_seconds"]-attempt.get("seconds",0))
                r["status"] = "pending"
    write_modules(work,state)
    codex = config["codex"]
    attempted_functions = sum(bool(r["attempts"]) for r in state["functions"].values())
    for address in state["order"] + state["cycles_and_dependents"]:
        row = state["functions"][address]
        node = graph["nodes"][address]
        if row["status"] in SUCCESS or row["status"] == "needs_human":
            continue
        contract = config["contracts"].get(address)
        if not contract and config.get("infer_scalars",False):
            contract = infer_scalar_contract(node)
        deps = [b for a,b in graph["edges"] if a == address]
        unsatisfied = [d for d in deps if state["functions"].get(d,{}).get("status") not in SUCCESS]
        reason = ("external import requires verified wrapper" if node.get("external") else
                  "cycle or ancestor of cycle" if address in state["cycles_and_dependents"] else
                  "unverified callees: "+", ".join(unsatisfied) if unsatisfied else
                  "no reviewed ABI/vector contract" if not contract else
                  "decompilation unavailable" if not node.get("completed") else None)
        if reason:
            row.update(status="blocked",reason=reason)
            continue
        if not row["attempts"]:
            if attempted_functions >= config["max_functions"]:
                row.update(status="blocked",reason="function-count budget")
                continue
            attempted_functions += 1
        contract = copy.deepcopy(contract)
        for recording in contract.get("recorded_files",[]):
            path = Path(recording["path"]).resolve(strict=True)
            if digest(path) != recording["sha256"]:
                raise ValueError("recorded input identity changed")
            contract.setdefault("recorded",[]).extend(read(path))
        rows = generate(contract,config["seed"])
        directory = out/"functions"/address
        directory.mkdir(parents=True,exist_ok=True)
        write(directory/"vectors.json",rows)
        write(directory/"contract.json",contract)
        feedback = row.get("feedback")
        for number in range(len(row["attempts"])+1,config["attempts"]+1):
            remaining = config["function_seconds"]-row["seconds"]
            if remaining <= 0:
                break
            budget = min(config["attempt_seconds"],remaining)
            attempt = directory/f"attempt-{number:02d}"
            attempt.mkdir()
            started = time.monotonic()
            deadline = started+budget
            rec = {"number":number,"status":"running","reserved_seconds":budget}
            row["attempts"].append(rec)
            row.update(status="translating",reason="")
            progress(out,state)
            try:
                signatures = {d:state["functions"][d]["rust_signature"] for d in deps}
                referenced_imports = [i for i in graph["imports"] if re.search(
                    r"\b"+re.escape(i["name"])+r"\s*\(",clean_c(node["c"]))]
                prompt = prompt_for(node,contract,signatures,referenced_imports,config["fma"],feedback)
                (attempt/"prompt.txt").write_text(prompt,encoding="utf-8")
                schema = {"type":"object","properties":{"code":{"type":"string"},"notes":{"type":"string"}},
                          "required":["code","notes"],"additionalProperties":False}
                write(attempt/"schema.json",schema)
                argv = [codex,"exec","--ignore-user-config","--ephemeral","--skip-git-repo-check",
                        "-C",attempt,"-s","read-only","--json","--color","never",
                        "-c",'project_doc_max_bytes=0',"-c",'features.shell_tool=false',
                        "-c",'features.multi_agent=false',
                        "-c",'features.apps=false',"-c",'web_search="disabled"',
                        "-c",f'model_reasoning_effort="{config["effort"]}"',
                        "--output-schema",attempt/"schema.json","-o",attempt/"answer.json"]
                if config.get("model"):
                    argv += ["-m",config["model"]]
                argv += ["-"]
                result = run(argv,attempt/"codex",min(config["generation_seconds"],deadline-time.monotonic()),
                             cwd=attempt,stdin=attempt/"prompt.txt")
                rec["generation_seconds"] = result["seconds"]
                events = []
                for line in (attempt/"codex/stdout.txt").read_text(encoding="utf-8",errors="replace").splitlines():
                    try:
                        events.append(json.loads(line))
                    except ValueError:
                        pass
                rec["usage"] = [e["usage"] for e in events if "usage" in e]
                tool_events = [e for e in events if e.get("item",{}).get("type") in
                               {"command_execution","mcp_tool_call","web_search","file_change"}]
                if tool_events:
                    raise ValueError("generator used tools; source-blind evaluation invalid")
                if result["timeout"] or result["returncode"]:
                    raise RuntimeError("Codex timed out/failed: "+(attempt/"codex/stderr.txt").read_text(encoding="utf-8",errors="replace")[-2000:])
                answer = read(attempt/"answer.json")
                code = answer["code"]
                validate_source(code,f"autoport_{address}")
                source = work/"src/autoport"/f"f_{address}.rs"
                source.write_text(code,encoding="utf-8")
                (attempt/"function.rs").write_text(code,encoding="utf-8")
                write_modules(work,state,address)
                build = run(["cargo","build","--release","--offline","--manifest-path",work/"Cargo.toml","-j","2"],
                    attempt/"build",deadline-time.monotonic(),env={"CARGO_TARGET_DIR":str(work/"target")})
                if build["timeout"] or build["returncode"]:
                    raise RuntimeError("Rust build failure: "+(attempt/"build/stderr.txt").read_text(encoding="utf-8",errors="replace")[-4000:])
                dll = work/"target/release"/(config["crate_name"].replace("-","_")+".dll")
                verdict = verify(contract,rows,config,address,graph,dll,attempt,deadline)
                if verdict["exact"]:
                    rec["status"] = "verified"
                    row.update(status="verified",source_sha256=digest(source),rust_signature=contract["rust_signature"],vectors=len(rows))
                else:
                    rec["status"] = "mismatch"
                    feedback = verdict
                    row["feedback"] = feedback
            except (OSError,ValueError,RuntimeError,TimeoutError,KeyError) as error:
                rec["status"] = "error"
                feedback = {"error":str(error)}
                row["feedback"] = feedback
                write(attempt/"failure.json",feedback)
            finally:
                rec["seconds"] = time.monotonic()-started
                row["seconds"] += rec["seconds"]
                if row["status"] != "verified":
                    row["status"] = "pending"
                progress(out,state)
            print(f"{config['program']} {address}: {rec['status']} {rec['seconds']:.3f}s",flush=True)
            if row["status"] == "verified":
                break
        if row["status"] != "verified":
            row.update(status="needs_human",reason="attempt/time budget exhausted; see retained feedback")
        write_modules(work,state)
        progress(out,state)
    progress(out,state)
    if config.get("annotate",True):
        annotate(config,graph,state,out)
    if config.get("oracle",True) and "oracle" not in state:
        final_oracle(config,out,state,graph)
    else:
        state["status"] = state.get("status") if "oracle" in state else "needs_human"
    progress(out,state)
    return 0 if state["status"] == "complete" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--model")
    parser.add_argument("--effort",choices=["low","medium","high","xhigh"])
    parser.add_argument("--codex")
    args = parser.parse_args()
    config = {"hub":"http://127.0.0.1:8766","max_nodes":120,"max_functions":8,"attempts":2,
              "generation_seconds":120,"attempt_seconds":180,"function_seconds":360,
              "witness_seconds":20,"setup_seconds":300,"oracle_seconds":600,
              "seed":20261112,"fma":"fma","effort":"low",**read(args.config)}
    for key in ["model","effort","codex"]:
        if getattr(args,key):
            config[key] = getattr(args,key)
    config["codex"] = config.get("codex") or codex_executable()
    config["aex"] = str(Path(config["aex"]).resolve(strict=True))
    for key in ["generation_seconds","attempt_seconds","function_seconds","witness_seconds","setup_seconds","oracle_seconds"]:
        if not isinstance(config[key],(int,float)) or not math.isfinite(config[key]) or config[key] <= 0:
            raise ValueError(f"positive finite {key} required")
    for key in ["attempts","max_nodes","max_functions"]:
        if type(config[key]) is not int or config[key] < 1:
            raise ValueError(f"positive integer {key} required")
    if config["fma"] not in {"fma","no-fma"}:
        raise ValueError("choose an explicit FMA lane")
    return execute(config,args.out)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted; owned children cleaned, resume with the same config.",file=sys.stderr)
        raise SystemExit(130)
