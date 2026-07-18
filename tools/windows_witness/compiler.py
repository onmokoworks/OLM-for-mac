"""Compile a witness-spec JSON document into a sendable Windows package."""

from __future__ import annotations

import argparse
import json
import shutil
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from .core import ID_RE, SpecError, canonical_json, deterministic_zip, sha256_file, validate_spec


HERE = Path(__file__).resolve().parent
COLLECTOR_PLACEHOLDER_RE = re.compile(r"\{\{([^{}]+)\}\}")
COLLECTOR_STATIC_PLACEHOLDERS = {"RUN_ID", "AE_PID", "CASE_ID", "OUTPUT_DIR"}
RUNTIME_FILES = {
    "artifacts/run_witness.ps1": HERE / "runtime" / "run_witness.ps1",
    "scripts/witness_runtime.py": HERE / "runtime.py",
}
FRIDA_RUNTIME_FILES = {
    "scripts/frida_runner.py": HERE / "frida_runner.py",
    "frida/agent.js": HERE / "frida" / "agent.js",
}


def _queue_source(contract: dict[str, Any]) -> str:
    cases = json.dumps(
        [{"id": case["id"], "bits_per_channel": case["bits_per_channel"]} for case in contract["cases"]],
        ensure_ascii=True,
    )
    request_id = json.dumps(contract["request_id"], ensure_ascii=True)
    environment = json.dumps(contract["project"].get("environment", {}), ensure_ascii=True, sort_keys=True)
    return f'''/* Generated serial AE witness queue. Common behavior; probes live in CDB templates. */
(function () {{
    function env(name) {{ try {{ return $.getenv(name) || ""; }} catch (_) {{ return ""; }} }}
    function write(path, value, append) {{
        var file = new File(path); file.encoding = "UTF-8";
        if (!file.open(append ? "a" : "w")) {{ throw new Error("could not write " + path); }}
        file.write(value); file.close();
    }}
    function read(path) {{
        var file = new File(path); file.encoding = "UTF-8";
        if (!file.open("r")) {{ throw new Error("could not read " + path); }}
        var value = file.read(); file.close();
        return value;
    }}
    function parseJson(path) {{ return eval("(" + read(path) + ")"); }}
    var bootstrapPath = File($.fileName).parent.fsName + "/queue_bootstrap.log";
    var work = env("WINDOWS_WITNESS_WORK_ROOT");
    var runId = env("WINDOWS_WITNESS_RUN_ID");
    var launcherRequestId = env("WINDOWS_WITNESS_REQUEST_ID");
    var root = env("WINDOWS_WITNESS_PACKAGE_ROOT") || File($.fileName).parent.parent.fsName;
    root = new Folder(root).fsName;
    var queueSha256 = env("WINDOWS_WITNESS_QUEUE_SHA256");
    var expectedRequestId = {request_id};
    if (!launcherRequestId || launcherRequestId !== expectedRequestId) {{
        throw new Error("launcher request_id does not match the compiled contract");
    }}
    var requestDir = new Folder(root + "/request").fsName;
    var requestManifest = parseJson(requestDir + "/request_manifest.json");
    if (!requestManifest || requestManifest.request_id !== expectedRequestId) {{
        throw new Error("request manifest request_id does not match the compiled contract");
    }}
    var bootstrapTempPath = bootstrapPath + ".tmp";
    write(bootstrapTempPath, "WITNESS_QUEUE_BOOTSTRAP\\n" +
        "run_id=" + runId + "\\n" +
        "work=" + work + "\\n" +
        "root=" + root + "\\n" +
        "request_id=" + expectedRequestId + "\\n" +
        "queue_sha256=" + queueSha256 + "\\n", false);
    if (!(new File(bootstrapTempPath)).rename("queue_bootstrap.log")) {{
        throw new Error("could not publish queue bootstrap marker");
    }}
    var cases = {cases};
    var extraEnvironment = {environment};
    var rendererSource = read(root + "/scripts/renderer.jsx");
    if (!work || !runId || !root || !queueSha256) {{ throw new Error("WINDOWS_WITNESS queue binding is required"); }}
    var queueLog = work + "/queue.log";
    write(queueLog, "WITNESS_QUEUE_START run_id=" + runId + "\\n", false);
    for (var i = 0; i < cases.length; i++) {{
        var caseId = cases[i].id;
        var caseBitsPerChannel = Number(cases[i].bits_per_channel);
        if (caseBitsPerChannel !== 8 && caseBitsPerChannel !== 16 && caseBitsPerChannel !== 32) {{
            throw new Error("invalid case bits_per_channel for " + caseId);
        }}
        $.setenv("OLM_AE_REQUEST_DIR", requestDir);
        $.setenv("OLM_AE_REQUEST_ID", expectedRequestId);
        $.setenv("OLM_AE_CASE_ID", caseId);
        $.setenv("OLM_AE_BITS_PER_CHANNEL", String(caseBitsPerChannel));
        $.setenv("OLM_AE_OUTPUT_DIR", work + "/exports/" + caseId);
        $.setenv("OLM_AE_LOG_PATH", work + "/ae_" + caseId + ".log");
        $.setenv("OLM_AE_RESULT_JSON", work + "/ae_result_" + caseId + ".json");
        $.setenv("OLM_AE_READY_MARKER", work + "/ready_" + caseId + ".marker");
        $.setenv("OLM_AE_CONTINUE_MARKER", work + "/continue_" + caseId + ".marker");
        $.setenv("OLM_AE_KEEP_OPEN", i === cases.length - 1 ? "0" : "1");
        $.setenv("OLM_AE_FORCE_NEW_PROJECT", i === 0 ? "1" : "0");
        if (app.project) {{ app.project.bitsPerChannel = caseBitsPerChannel; }}
        for (var key in extraEnvironment) {{
            if (extraEnvironment.hasOwnProperty(key)) {{ $.setenv(key, String(extraEnvironment[key])); }}
        }}
        write(queueLog, "WITNESS_CASE_START run_id=" + runId + " case_id=" + caseId + "\\n", true);
        // `-r` already owns AE's script slot. evalFile would be rejected as a
        // second script unless AE is launched with an override flag.
        eval(rendererSource);
        var result = parseJson(work + "/ae_result_" + caseId + ".json");
        var observedBitsPerChannel = result.project_bits_per_channel;
        if (observedBitsPerChannel === undefined && app.project) {{
            observedBitsPerChannel = app.project.bitsPerChannel;
        }}
        if (Number(observedBitsPerChannel) !== caseBitsPerChannel) {{
            throw new Error("renderer bitsPerChannel does not match case contract for " + caseId);
        }}
        if (app.project) {{ app.project.bitsPerChannel = caseBitsPerChannel; }}
        write(queueLog, "WITNESS_CASE_END run_id=" + runId + " case_id=" + caseId + "\\n", true);
    }}
    write(queueLog, "WITNESS_QUEUE_END run_id=" + runId + "\\n", true);
}}());
'''


def _package_readme(contract: dict[str, Any]) -> str:
    cases = ", ".join(f"`{case['id']}`" for case in contract["cases"])
    transport_kind = contract.get("transport", {}).get("kind", "cdb")
    collector = transport_kind == "in_process_collector"
    frida = transport_kind == "frida"
    if transport_kind == "cdb":
        return f"""# {contract['request_id']} Windows Witness

This package was generated by `tools/windows_witness` contract version 1.
It runs {cases} serially in one fresh desktop After Effects process using the
hash-pinned `{contract['plugin']['module_filename']}` at
`{contract['project']['bits_per_channel']}bpc` with the Software renderer.

Run from an interactive Windows desktop PowerShell session:

```powershell
.\\artifacts\\run_witness.ps1
```

The launcher waits for each renderer to report `effect_loaded=1` and
`parameters_applied=1`, binds exactly one AE PID and loaded module base across
all cases, arms CDB, and only then releases the renderer. Success requires all
event cardinalities, required fields, identity constraints, render results,
and required exports in `witness-contract.json`. Every other outcome is
`exact_bind_failure`; a deterministic return ZIP is still produced with the
available diagnostics.

Runtime requirements: Windows PowerShell 5.1+, desktop After Effects, CDB, and
the Python 3 launcher `py -3`.
"""
    transport_requirements = (
        "the packaged injector and collector DLL"
        if collector
        else "the Python `frida` package and the packaged Frida agent"
    )
    capture_sentence = (
        "injects the configured collector into the exact AE PID and requires valid collector outputs"
        if collector
        else "attaches Frida to the exact AE PID, arms the configured entry/core hooks, and only then releases the renderer"
    )
    return f"""# {contract['request_id']} Windows Witness

This package was generated by `tools/windows_witness` contract version 1.
It runs {cases} serially in one fresh desktop After Effects process using the
hash-pinned `{contract['plugin']['module_filename']}` at
`{contract['project']['bits_per_channel']}bpc` with the Software renderer.

Run from an interactive Windows desktop PowerShell session:

```powershell
.\\artifacts\\run_witness.ps1
```

The launcher waits for each renderer to report `effect_loaded=1` and
`parameters_applied=1`, binds exactly one AE PID and loaded module base across
all cases, {capture_sentence}. Success requires all
event cardinalities, required fields, identity constraints, render results,
and required exports in `witness-contract.json`. Every other outcome is
`exact_bind_failure`; a deterministic return ZIP is still produced with the
available diagnostics.

Runtime requirements: Windows PowerShell 5.1+, desktop After Effects,
{transport_requirements}, and the Python 3 launcher `py -3`.
"""


def _normalized_contract(spec: dict[str, Any]) -> dict[str, Any]:
    contract = deepcopy(spec)
    transport = spec.get("transport", {"kind": "cdb"})
    contract["contract_kind"] = {
        "cdb": "windows_ae_cdb_witness_m0",
        "in_process_collector": "windows_ae_collector_witness_m0",
        "frida": "windows_ae_frida_witness_m1",
    }[transport["kind"]]
    contract["success_status"] = "answered"
    contract["failure_status"] = "exact_bind_failure"
    contract["queue"] = "scripts/ae_witness_queue.jsx"
    contract["renderer"]["package_path"] = "scripts/renderer.jsx"
    contract["request_assets"]["package_path"] = "request"
    for index, case in enumerate(contract["cases"]):
        case["order"] = index
        if transport["kind"] == "cdb":
            case["package_cdb_template"] = f"cdb/{index:03d}_{case['id']}.cdb.in"
    core_logs = [
        "afterfx_launcher_stdout.txt",
        "afterfx_launcher_stderr.txt",
        "afterfx_process_diagnostics.json",
        "afterfx_bootstrap.cdb",
        "afterfx_bootstrap_cdb_trace.txt",
        "afterfx_launch_wrapper.cmd",
        "launched_queue.jsx",
        "queue_bootstrap.log",
        "queue.log",
        "combined_cdb_trace.txt",
        "capture_diagnostics.json",
        "runtime_identity.json",
        "validation_status.json",
    ]
    if contract["plugin"].get("cache_rescan") is True:
        core_logs.append("plugin_cache_rescan.json")
    for case in contract["cases"]:
        case_id = case["id"]
        core_logs.extend([
            f"ready_{case_id}.marker",
            f"continue_{case_id}.marker",
        ])
        if transport["kind"] == "cdb":
            core_logs.extend([
                f"probe_{case_id}.cdb", f"cdb_trace_{case_id}.txt",
                f"cdb_stdout_{case_id}.txt", f"cdb_stderr_{case_id}.txt",
            ])
        elif transport["kind"] == "in_process_collector":
            for output in transport["required_outputs"]:
                core_logs.append(f"collector_{case_id}_{Path(output).name}")
            core_logs.append(f"collector_config_{case_id}.json")
            core_logs.extend([f"collector_stdout_{case_id}.txt", f"collector_stderr_{case_id}.txt"])
        else:
            case["package_frida_contract"] = "witness-contract.json"
            core_logs.extend([
                f"frida_{case_id}/armed.json",
                f"frida_{case_id}/events.jsonl",
                f"frida_{case_id}/result-manifest.json",
                f"frida_stdout_{case_id}.txt",
                f"frida_stderr_{case_id}.txt",
            ])
        core_logs.extend([f"ae_{case_id}.log", f"ae_result_{case_id}.json"])
    if transport["kind"] == "in_process_collector":
        contract["transport"] = dict(transport)
        contract["transport"].update({
            "package_injector_path": "collector/injector.exe",
            "package_collector_dll": "collector/collector.dll",
            "package_config_template": "collector/config.json.in",
            "arm_timeout_seconds": int(transport.get("arm_timeout_seconds", 30)),
            "capture_timeout_seconds": int(transport.get("capture_timeout_seconds", 60)),
        })
    elif transport["kind"] == "frida":
        contract["transport"] = dict(transport)
        contract["transport"].update({
            "package_runner_path": "scripts/frida_runner.py",
            "package_agent_path": "frida/agent.js",
            "arm_timeout_seconds": int(transport.get("arm_timeout_seconds", 30)),
            "capture_timeout_seconds": int(transport.get("capture_timeout_seconds", 60)),
        })
    contract["return_bundle"]["include_logs"] = list(dict.fromkeys(core_logs + contract["return_bundle"].get("include_logs", [])))
    return contract


def compile_witness(spec_path: Path, output_dir: Path, zip_path: Path | None = None) -> tuple[Path, Path]:
    """Compile *spec_path* and return the package directory and deterministic ZIP."""

    spec_path = spec_path.resolve()
    spec = _load_spec_for_compiler(spec_path)
    base = spec_path.parent
    output_dir = output_dir.resolve()
    archive = (zip_path.resolve() if zip_path else output_dir.with_suffix(".zip"))
    if output_dir == archive or output_dir in archive.parents:
        raise ValueError("zip path must be outside the package directory")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    contract = _normalized_contract(spec)
    transport = spec.get("transport", {"kind": "cdb"})

    shutil.copytree(base / spec["request_assets"]["source"], output_dir / "request")
    (output_dir / "scripts").mkdir()
    (output_dir / "artifacts").mkdir()
    (output_dir / "cdb").mkdir()
    shutil.copy2(base / spec["renderer"]["source"], output_dir / "scripts" / "renderer.jsx")
    for destination, source in RUNTIME_FILES.items():
        shutil.copy2(source, output_dir / destination)
    if transport["kind"] == "frida":
        for destination, source in FRIDA_RUNTIME_FILES.items():
            target = output_dir / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    (output_dir / "scripts" / "ae_witness_queue.jsx").write_text(_queue_source(contract), encoding="utf-8", newline="\n")
    (output_dir / "README.md").write_text(_package_readme(contract), encoding="utf-8", newline="\n")

    if transport["kind"] == "cdb":
        for case, compiled_case in zip(spec["cases"], contract["cases"]):
            source = base / case["cdb_template"]
            destination = output_dir / compiled_case["package_cdb_template"]
            destination.write_text(source.read_text(encoding="utf-8"), encoding="ascii", newline="\n")
    elif transport["kind"] == "in_process_collector":
        for source_key, destination_name in (
            ("injector_path", "collector/injector.exe"),
            ("collector_dll", "collector/collector.dll"),
            ("config_template", "collector/config.json.in"),
        ):
            source = base / transport[source_key]
            destination = output_dir / destination_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    contract_path = output_dir / "witness-contract.json"
    contract_path.write_bytes(canonical_json(contract))
    inventory: list[dict[str, Any]] = []
    for path in sorted((path for path in output_dir.rglob("*") if path.is_file()), key=lambda item: item.relative_to(output_dir).as_posix()):
        inventory.append({
            "path": path.relative_to(output_dir).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    manifest = {
        "schema_version": 1,
        "kind": "windows_witness_generated_package",
        "request_id": spec["request_id"],
        "contract": "witness-contract.json",
        "entrypoint": "artifacts/run_witness.ps1",
        "files": inventory,
    }
    if "queue" in spec:
        manifest["queue"] = spec["queue"]
    (output_dir / "package-manifest.json").write_bytes(canonical_json(manifest))
    deterministic_zip(output_dir, archive)
    return output_dir, archive


def _load_spec_for_compiler(spec_path: Path) -> dict[str, Any]:
    """Load legacy specs through the original validator and collector specs through its shared rules."""
    try:
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecError(f"could not read spec {spec_path}: {exc}") from exc
    _validate_plugin_cache_rescan(raw)
    transport = raw.get("transport", {"kind": "cdb"})
    compatibility = deepcopy(raw)
    compatibility.get("plugin", {}).pop("cache_rescan", None)
    if not isinstance(transport, dict) or transport.get("kind") == "cdb":
        validate_spec(compatibility, spec_path.parent)
        return raw
    if transport.get("kind") not in {"in_process_collector", "frida"}:
        raise SpecError("transport.kind must be cdb, in_process_collector, or frida")
    compatibility.pop("transport", None)
    compatibility.setdefault("host", {}).setdefault("cdb_path", "collector-compat-cdb.exe")
    compatibility["cdb"] = {"armed_marker": "collector_compat", "arm_timeout_seconds": 1, "capture_timeout_seconds": 1}
    for case in compatibility.get("cases", []):
        case.setdefault("cdb_template", "collector_compat.cdb.in")
    validate_spec(compatibility, None)
    if transport["kind"] == "in_process_collector":
        _validate_collector_transport(raw, spec_path.parent)
    else:
        _validate_frida_transport(raw, spec_path.parent)
    return raw


def _validate_plugin_cache_rescan(spec: dict[str, Any]) -> None:
    plugin = spec.get("plugin")
    if not isinstance(plugin, dict):
        raise SpecError("plugin must be an object")
    if "cache_rescan" in plugin and type(plugin["cache_rescan"]) is not bool:
        raise SpecError("plugin.cache_rescan must be boolean")


def _validate_collector_transport(spec: dict[str, Any], base: Path) -> None:
    transport = spec.get("transport")
    if not isinstance(transport, dict):
        raise SpecError("spec.transport must be an object")
    allowed = {"kind", "injector_path", "collector_dll", "config_template", "required_outputs", "arm_timeout_seconds", "capture_timeout_seconds"}
    extra = set(transport) - allowed
    if extra:
        raise SpecError(f"spec.transport has unknown keys: {', '.join(sorted(extra))}")
    required = {"kind", "injector_path", "collector_dll", "config_template", "required_outputs"}
    missing = required - set(transport)
    if missing:
        raise SpecError(f"spec.transport missing keys: {', '.join(sorted(missing))}")
    for key in ("injector_path", "collector_dll", "config_template"):
        value = transport[key]
        if not isinstance(value, str) or not value or value.startswith(("/", "\\")) or ".." in Path(value).parts:
            raise SpecError(f"spec.transport.{key} must be a safe relative path")
        path = base / value
        if not path.is_file():
            raise SpecError(f"missing collector asset: {path}")
    outputs = transport["required_outputs"]
    if not isinstance(outputs, list) or not outputs or any(not isinstance(output, str) for output in outputs) or len(outputs) != len(set(outputs)):
        raise SpecError("spec.transport.required_outputs must be a non-empty unique array")
    for output in outputs:
        if not isinstance(output, str) or not output or output.startswith(("/", "\\")) or ".." in Path(output).parts:
            raise SpecError("spec.transport.required_outputs must contain safe relative paths")
    if not {"collector_trace.txt", "collector_status.json"}.issubset(outputs):
        raise SpecError("spec.transport.required_outputs must include collector_trace.txt and collector_status.json")
    basenames = [Path(output).name for output in outputs]
    if len(basenames) != len(set(basenames)):
        raise SpecError("spec.transport.required_outputs must have unique basenames")
    for key in ("arm_timeout_seconds", "capture_timeout_seconds"):
        timeout = transport.get(key, 30 if key == "arm_timeout_seconds" else 60)
        if type(timeout) is not int or timeout < 1:
            raise SpecError(f"spec.transport.{key} must be a positive integer")
    template = (base / transport["config_template"]).read_text(encoding="utf-8")
    placeholders = set(COLLECTOR_PLACEHOLDER_RE.findall(template))
    for placeholder in placeholders:
        if placeholder in COLLECTOR_STATIC_PLACEHOLDERS:
            continue
        if placeholder.startswith("CASE_VALUE:") and all(placeholder[11:] in case.get("template_values", {}) for case in spec["cases"]):
            continue
        raise SpecError(f"collector config has unsupported or unresolved placeholder {{{{{placeholder}}}}}")
    renderer = base / spec["renderer"]["source"]
    assets = base / spec["request_assets"]["source"]
    if not renderer.is_file():
        raise SpecError(f"missing renderer source: {renderer}")
    if not assets.is_dir():
        raise SpecError(f"missing request assets: {assets}")
    manifest = assets / "request_manifest.json"
    if not manifest.is_file():
        raise SpecError(f"missing request manifest: {manifest}")
    try:
        embedded = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecError(f"could not read embedded request manifest {manifest}: {exc}") from exc
    if not isinstance(embedded, dict) or not isinstance(embedded.get("request_id"), str) or ID_RE.fullmatch(embedded["request_id"]) is None:
        raise SpecError(f"{manifest} request_id is invalid")
    if embedded["request_id"] != spec.get("request_id"):
        raise SpecError(f"{manifest} request_id must exactly match spec.request_id")


def _validate_frida_transport(spec: dict[str, Any], base: Path) -> None:
    transport = spec.get("transport")
    if not isinstance(transport, dict):
        raise SpecError("spec.transport must be an object")
    allowed = {"kind", "agent_config", "arm_timeout_seconds", "capture_timeout_seconds"}
    extra = set(transport) - allowed
    if extra:
        raise SpecError(f"spec.transport has unknown keys: {', '.join(sorted(extra))}")
    if "agent_config" not in transport or not isinstance(transport["agent_config"], dict):
        raise SpecError("spec.transport.agent_config must be an object")
    config = transport["agent_config"]
    module_name = config.get("module_name")
    if module_name != spec.get("plugin", {}).get("module_filename"):
        raise SpecError("spec.transport.agent_config.module_name must match plugin.module_filename")
    exports = config.get("exports", [])
    rvas = config.get("internal_rvas", [])
    if not isinstance(exports, list) or not isinstance(rvas, list) or not (exports or rvas):
        raise SpecError("spec.transport.agent_config requires exports or internal_rvas")
    for index, hook in enumerate(exports):
        if not isinstance(hook, dict) or not isinstance(hook.get("export"), str) or not hook["export"]:
            raise SpecError(f"spec.transport.agent_config.exports[{index}].export is required")
        if not isinstance(hook.get("name"), str) or not hook["name"]:
            raise SpecError(f"spec.transport.agent_config.exports[{index}].name is required")
        argument_count = hook.get("argument_count", 0)
        if type(argument_count) is not int or not 0 <= argument_count <= 16:
            raise SpecError(f"spec.transport.agent_config.exports[{index}].argument_count must be 0..16")
        reads = hook.get("reads", [])
        if not isinstance(reads, list):
            raise SpecError(f"spec.transport.agent_config.exports[{index}].reads must be an array")
        for read_index, read in enumerate(reads):
            where = f"spec.transport.agent_config.exports[{index}].reads[{read_index}]"
            if not isinstance(read, dict) or not isinstance(read.get("name"), str) or not read["name"]:
                raise SpecError(f"{where}.name is required")
            if not isinstance(read.get("source"), str) or re.fullmatch(r"arg\([0-9]+\)|retval", read["source"]) is None:
                raise SpecError(f"{where}.source must be arg(index) or retval")
            if read.get("type") not in {"u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64", "f32", "f64", "ptr", "bytes"}:
                raise SpecError(f"{where}.type is invalid")
            if "direct" in read and type(read["direct"]) is not bool:
                raise SpecError(f"{where}.direct must be boolean")
    for index, hook in enumerate(rvas):
        if not isinstance(hook, dict) or not isinstance(hook.get("rva"), int) or hook["rva"] < 0:
            raise SpecError(f"spec.transport.agent_config.internal_rvas[{index}].rva must be a nonnegative integer")
        if not isinstance(hook.get("name"), str) or not hook["name"]:
            raise SpecError(f"spec.transport.agent_config.internal_rvas[{index}].name is required")
    for key in ("arm_timeout_seconds", "capture_timeout_seconds"):
        timeout = transport.get(key, 30 if key == "arm_timeout_seconds" else 60)
        if type(timeout) is not int or timeout < 1:
            raise SpecError(f"spec.transport.{key} must be a positive integer")
    for path, label in ((base / spec["renderer"]["source"], "renderer"), (base / spec["request_assets"]["source"], "request assets")):
        if label == "renderer" and not path.is_file():
            raise SpecError(f"missing renderer source: {path}")
        if label == "request assets" and not path.is_dir():
            raise SpecError(f"missing request assets: {path}")
    manifest = base / spec["request_assets"]["source"] / "request_manifest.json"
    if not manifest.is_file():
        raise SpecError(f"missing request manifest: {manifest}")
    try:
        embedded = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecError(f"could not read embedded request manifest {manifest}: {exc}") from exc
    if not isinstance(embedded, dict) or embedded.get("request_id") != spec.get("request_id"):
        raise SpecError(f"{manifest} request_id must exactly match spec.request_id")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    args = parser.parse_args(argv)
    package, archive = compile_witness(args.spec, args.output_dir, args.zip_path)
    print(json.dumps({"status": "ok", "package": str(package), "zip": str(archive)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
