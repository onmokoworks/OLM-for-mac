#!/usr/bin/env python3
"""Fail-closed Windows AfterFX Frida capture controller.

The module deliberately has no import-time dependency on ``frida``.  This is
important because contracts and fixture captures are also validated on hosts
where the Windows Frida package is unavailable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any


HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
PAIR = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>[^\s]+)")


class RunnerError(RuntimeError):
    pass


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RunnerError(f"cannot read JSON {path}: {exc}") from exc


def _text(value: Any, label: str) -> str:
    if not isinstance(value, (str, int)) or not str(value).strip():
        raise RunnerError(f"contract identity {label} is missing or invalid")
    return str(value).strip()


def _first(contract: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value: Any = contract
        for part in path:
            if not isinstance(value, dict) or part not in value:
                break
            value = value[part]
        else:
            if value not in (None, ""):
                return value
    return None


def load_contract(path: Path, run_id_override: str | None = None) -> dict[str, Any]:
    value = _json(path)
    if not isinstance(value, dict):
        raise RunnerError("contract root must be a JSON object")
    run_id = run_id_override or _first(value, ("run_id",), ("identity", "run_id"), ("run", "run_id"))
    if run_id is None and value.get("run_id_prefix") and run_id_override:
        run_id = run_id_override
    module = _first(value, ("module", "filename"), ("module_filename",), ("plugin", "module_filename"), ("plugin", "module"), ("identity", "module"))
    sha = _first(value, ("aex_sha256",), ("plugin", "aex_sha256"), ("identity", "aex_sha256"))
    cases = value.get("cases")
    if cases is None:
        case_id = _first(value, ("case_id",), ("run", "case_id"), ("identity", "case_id"), ("case", "id"))
        cases = [{"id": case_id}] if case_id else []
    if not isinstance(cases, list) or not cases:
        raise RunnerError("contract must contain a non-empty cases list")
    case_ids: list[str] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise RunnerError(f"contract cases[{index}] must be an object")
        case_ids.append(_text(case.get("id"), f"cases[{index}].id"))
    if len(set(case_ids)) != len(case_ids):
        raise RunnerError("contract case ids must be unique")
    run_id = _text(run_id, "run_id")
    module = _text(module, "module_filename")
    sha = _text(sha, "aex_sha256").lower()
    if HEX64.fullmatch(sha) is None:
        raise RunnerError("contract identity aex_sha256 must be 64 hexadecimal characters")
    renderer = _first(value, ("project", "renderer"), ("identity", "renderer"), ("renderer",))
    if isinstance(renderer, dict):
        raise RunnerError("contract renderer identity must be a string")
    bpc = _first(value, ("project_bpc",), ("bitdepth",), ("project", "bits_per_channel"), ("identity", "project_bpc"))
    if renderer is None or bpc is None:
        raise RunnerError("contract must provide renderer and project bits_per_channel")
    timeout = _first(
        value,
        ("timeout_seconds",),
        ("capture_timeout_seconds",),
        ("transport", "capture_timeout_seconds"),
        ("timeouts", "capture_seconds"),
        ("timeouts", "trace_ms"),
        ("cdb", "capture_timeout_seconds"),
    )
    try:
        timeout = float(timeout if timeout is not None else 60)
        if _first(value, ("timeouts", "trace_ms")) is not None:
            timeout /= 1000.0
        if _first(value, ("transport", "kind")) == "frida":
            timeout += float(_first(value, ("transport", "arm_timeout_seconds")) or 30)
    except (TypeError, ValueError) as exc:
        raise RunnerError("contract timeout_seconds must be numeric") from exc
    if timeout <= 0:
        raise RunnerError("contract timeout_seconds must be greater than zero")
    value["_runner"] = {"run_id": run_id, "module": module, "aex_sha256": sha,
                         "case_ids": case_ids, "renderer": str(renderer),
                         "project_bpc": str(bpc), "timeout": timeout}
    known_pid = _first(value, ("run", "pid"), ("pid",), ("identity", "ae_pid"))
    known_base = _first(value, ("run", "module_base"), ("module_base",), ("identity", "module_base"))
    if known_pid is not None:
        value["_runner"]["ae_pid"] = str(known_pid)
    if known_base is not None:
        value["_runner"]["module_base"] = str(known_base)
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _identity(contract: dict[str, Any], observed: dict[str, Any], pid: int | None) -> dict[str, str]:
    expected = contract["_runner"]
    required = {
        "run_id": expected["run_id"], "module": expected["module"],
        "aex_sha256": expected["aex_sha256"], "renderer": expected["renderer"],
        "project_bpc": expected["project_bpc"],
    }
    if pid is not None:
        required["ae_pid"] = str(pid)
    for key, value in required.items():
        actual = observed.get(key)
        if key == "module":
            actual = observed.get("module") or observed.get("module_filename") or observed.get("module_name")
        if actual is not None and str(actual).lower() != str(value).lower():
            raise RunnerError(f"identity mismatch for {key}: expected {value!r}, got {actual!r}")
    observed_module = observed.get("module") or observed.get("module_filename") or observed.get("module_name")
    missing = [key for key in ("run_id", "aex_sha256", "module_base") if key not in observed]
    if not observed_module:
        missing.append("module")
    if pid is None and "ae_pid" not in observed:
        missing.append("ae_pid")
    if missing:
        raise RunnerError("capture did not prove required identity: " + ", ".join(sorted(set(missing))))
    if not str(observed.get("module_base", "")).strip():
        raise RunnerError("capture did not prove a non-empty module_base")
    result = {key: str(observed.get(key, value)) for key, value in required.items()}
    result["module"] = str(observed_module)
    return result


def _event_specs(contract: dict[str, Any]) -> list[dict[str, Any]]:
    specs = _first(contract, ("validation", "events"), ("events",)) or []
    if isinstance(specs, dict):
        return [{"name": name, "prefix": name, "cardinality": {"scope": "global", "min": count, "max": count}}
                for name, count in specs.items()]
    if not isinstance(specs, list):
        raise RunnerError("contract validation.events must be a list")
    return [spec for spec in specs if isinstance(spec, dict)]


def _event_target(contract: dict[str, Any], raw_name: str) -> dict[str, Any]:
    specs = _event_specs(contract)
    name = raw_name.lower()
    candidates = [spec for spec in specs if str(spec.get("name", "")).lower() == name or str(spec.get("prefix", "")).lower() == name]
    if not candidates:
        candidates = [spec for spec in specs if name in str(spec.get("name", "")).lower() or name in str(spec.get("prefix", "")).lower()]
    if not candidates and len(specs) == 1:
        candidates = specs
    if len(candidates) != 1:
        raise RunnerError(f"agent event {raw_name!r} does not map uniquely to a contract event")
    return candidates[0]


def _payload_object(payload: Any) -> dict[str, Any]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RunnerError(f"agent payload is not JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RunnerError("agent payload must be a JSON object")
    return payload


def _event_from_message(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, dict) and str(payload.get("type", payload.get("kind", "event"))).lower() in {"event", "capture", "json"}:
        value = payload.get("event", payload.get("record", payload))
        return value if isinstance(value, dict) else None
    if isinstance(payload, str):
        try:
            value = json.loads(payload)
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            fields = {m.group("key"): m.group("value") for m in PAIR.finditer(payload)}
            prefix = payload.split(None, 1)[0] if payload.split() else ""
            if prefix:
                fields.setdefault("prefix", prefix)
            return fields or None
    return payload if isinstance(payload, dict) else None


def validate_capture(contract: dict[str, Any], events: list[dict[str, Any]], observed: dict[str, Any], pid: int | None = None, case_id: str | None = None) -> dict[str, Any]:
    """Validate identity and event cardinality; raises on every mismatch."""
    identity = _identity(contract, observed, pid)
    cases = set(contract["_runner"]["case_ids"])
    specs = _event_specs(contract)
    if not specs:
        raise RunnerError("contract has no validation event specifications")
    for index, event in enumerate(events):
        case_id = event.get("case_id")
        if case_id not in cases:
            raise RunnerError(f"event {index} has unknown case_id {case_id!r}")
        for key in ("run_id", "aex_sha256", "ae_pid", "module_base"):
            if key in event and str(event[key]).lower() != str(observed.get(key, "")).lower():
                raise RunnerError(f"event {index} identity mismatch for {key}")
    for spec in specs:
        name = str(spec.get("name", spec.get("prefix", "event")))
        prefix = spec.get("prefix")
        matching = [event for event in events if event.get("event") == name or event.get("kind") == name or (prefix and event.get("prefix") == prefix)]
        card = spec.get("cardinality", {})
        minimum = int(card.get("min", 1))
        maximum = int(card.get("max", minimum))
        scopes = ([case_id] if case_id else contract["_runner"]["case_ids"]) if card.get("scope", "per_case") == "per_case" else [None]
        for case_id in scopes:
            scoped = matching if case_id is None else [e for e in matching if e.get("case_id") == case_id]
            if not minimum <= len(scoped) <= maximum:
                raise RunnerError(f"event {name} case {case_id or '*'} cardinality {len(scoped)}, expected {minimum}..{maximum}")
            for event in scoped:
                for field in spec.get("required_fields", []):
                    if field not in event or event[field] in (None, ""):
                        raise RunnerError(f"event {name} missing required field {field}")
                for field, constraint in spec.get("field_constraints", {}).items():
                    actual = str(event.get(field, ""))
                    if "equals" in constraint and actual != str(constraint["equals"]):
                        raise RunnerError(f"event {name} field {field} does not equal contract value")
                    if "pattern" in constraint and re.fullmatch(str(constraint["pattern"]), actual) is None:
                        raise RunnerError(f"event {name} field {field} fails contract pattern")
    return {"run_id": identity["run_id"], "ae_pid": int(identity.get("ae_pid", observed.get("ae_pid"))),
            "module": identity["module"], "module_base": str(observed["module_base"]),
            "aex_sha256": identity["aex_sha256"], "renderer": identity["renderer"],
            "project_bpc": identity["project_bpc"]}


class Capture:
    def __init__(self, contract: dict[str, Any], output: Path, pid: int | None, case_id: str | None = None):
        self.contract, self.output, self.pid, self.case_id = contract, output, pid, case_id
        self.events: list[dict[str, Any]] = []
        self.chunks: list[dict[str, Any]] = []
        self.observed: dict[str, Any] = {}
        self.error: str | None = None
        self.finished = threading.Event()
        self.started = time.monotonic()

    def _record(self, raw: dict[str, Any]) -> None:
        raw = _payload_object(raw)
        event_kind = str(raw.get("event", raw.get("kind", raw.get("type", "")))).lower()
        if event_kind in {"error", "agent_error", "exception"}:
            raise RunnerError(str(raw.get("message", raw.get("error", "agent error"))))
        if raw.get("run_id") not in (None, self.contract["_runner"]["run_id"]):
            raise RunnerError("agent run_id conflicts with controller contract")
        if event_kind == "module":
            module = raw.get("module") if isinstance(raw.get("module"), dict) else raw
            filename = module.get("filename", module.get("name", module.get("module_filename", module.get("path"))))
            base = module.get("base", module.get("module_base"))
            sha = module.get("sha256", module.get("aex_sha256", module.get("sha")))
            if filename is not None and str(filename).replace("\\", "/").rsplit("/", 1)[-1].lower() != self.contract["_runner"]["module"].lower():
                raise RunnerError(f"loaded module mismatch: expected {self.contract['_runner']['module']!r}, got {filename!r}")
            if sha is not None and str(sha).lower() != self.contract["_runner"]["aex_sha256"]:
                raise RunnerError("loaded module AEX SHA-256 does not match the contract")
            if not str(base or "").strip():
                raise RunnerError("module event has no module base")
            expected_base = self.contract["_runner"].get("module_base")
            if expected_base is not None and str(base).lower() != str(expected_base).lower():
                raise RunnerError(f"module base mismatch: expected {expected_base!r}, got {base!r}")
            if self.pid is None:
                self.pid = module.get("ae_pid", module.get("pid", raw.get("ae_pid", raw.get("pid"))))
            self.observed.update({"run_id": self.contract["_runner"]["run_id"], "module": filename,
                                  "module_base": str(base), "aex_sha256": self.contract["_runner"]["aex_sha256"]})
            self.events.append({"event": "module_loaded", "prefix": "module_loaded", "run_id": self.contract["_runner"]["run_id"],
                                "case_id": str(self.case_id or ""), "ae_pid": str(self.pid or ""),
                                "module_base": str(base), "aex_sha256": self.contract["_runner"]["aex_sha256"],
                                "renderer": self.contract["_runner"]["renderer"], "project_bpc": self.contract["_runner"]["project_bpc"]})
            return
        if event_kind in {"call", "return"}:
            if "module_base" not in self.observed:
                raise RunnerError("agent emitted a hook event before module identity")
            hook = raw.get("hook") if isinstance(raw.get("hook"), dict) else {}
            hook_name = str(hook.get("name", raw.get("hook_name", event_kind)))
            event_name = hook_name if event_kind == "call" else hook_name + "_return"
            try:
                spec = _event_target(self.contract, event_name)
            except RunnerError:
                if event_kind == "return":
                    return
                raise
            fields = raw.get("fields") if isinstance(raw.get("fields"), dict) else {}
            if isinstance(raw.get("data"), dict):
                fields = {**raw["data"], **fields}
            canonical = dict(fields)
            for key, value in raw.items():
                if key not in {"schema", "sequence", "timestamp", "thread_id", "event", "kind", "type", "module", "fields"}:
                    canonical.setdefault(key, value)
            if hook:
                canonical["hook_meta"] = hook
                canonical["hook"] = hook_name
                if "rva" in hook:
                    canonical["rva"] = hook["rva"]
            reads = raw.get("reads")
            if isinstance(reads, dict):
                canonical["reads"] = reads
                for read_name, read_value in reads.items():
                    if isinstance(read_value, dict):
                        canonical[f"{read_name}_type"] = read_value.get("type")
                        canonical[f"{read_name}_value"] = read_value.get("value")
            current_case = canonical.get("case_id", self.case_id)
            if not current_case:
                raise RunnerError("hook event has no case_id for the current invocation")
            if self.case_id and str(current_case) != self.case_id:
                raise RunnerError("agent case_id conflicts with current invocation")
            canonical.update({"event": spec.get("name", event_kind), "prefix": spec.get("prefix", spec.get("name", event_kind)),
                              "run_id": self.contract["_runner"]["run_id"], "case_id": str(current_case),
                              "ae_pid": str(self.pid if self.pid is not None else canonical.get("ae_pid", self.observed.get("ae_pid", ""))), "module_base": self.observed["module_base"],
                              "aex_sha256": self.contract["_runner"]["aex_sha256"],
                              "renderer": self.contract["_runner"]["renderer"], "project_bpc": self.contract["_runner"]["project_bpc"]})
            self.events.append(canonical)
            self.observed.update({"run_id": canonical["run_id"], "ae_pid": canonical["ae_pid"],
                                  "renderer": canonical["renderer"], "project_bpc": canonical["project_bpc"]})
            if self._complete():
                self.finished.set()
            return
        if event_kind in {"renderer_done", "render_complete", "lifecycle_complete", "complete", "done", "finished"}:
            self.finished.set()
            return
        if event_kind:
            raise RunnerError(f"unsupported agent event {event_kind!r}")

    def _complete(self) -> bool:
        for spec in _event_specs(self.contract):
            card = spec.get("cardinality", {})
            minimum = int(card.get("min", 1))
            maximum = int(card.get("max", minimum))
            name, prefix = spec.get("name"), spec.get("prefix")
            rows = [event for event in self.events if event.get("event") == name or event.get("prefix") == prefix]
            if self.case_id:
                rows = [event for event in rows if event.get("case_id") == self.case_id]
            if not minimum <= len(rows) <= maximum:
                return False
        return True

    def message(self, message: dict[str, Any], data: Any = None) -> None:
        payload = message.get("payload", message)
        try:
            if message.get("type") == "error":
                raise RunnerError(str(message.get("description") or payload or "agent error"))
            if isinstance(payload, str):
                payload_object = _payload_object(payload)
            else:
                payload_object = payload
        except RunnerError as exc:
            self.error = str(exc)
            self.finished.set()
            return
        kind = str(payload_object.get("type", payload_object.get("kind", ""))).lower() if isinstance(payload_object, dict) else ""
        if data is not None or kind in {"binary", "chunk", "bytes"}:
            blob = data if isinstance(data, (bytes, bytearray)) else (payload.get("data") if isinstance(payload, dict) else None)
            if isinstance(blob, str):
                blob = blob.encode("latin1")
            if not isinstance(blob, (bytes, bytearray)):
                raise RunnerError("agent binary message has no byte payload")
            self.chunks.append({"data": bytes(blob), "meta": payload if isinstance(payload, dict) else {}})
            return
        try:
            self._record(payload_object)
        except RunnerError as exc:
            self.error = str(exc)
            self.finished.set()
            return
        if self.events:
            return
        if isinstance(payload, dict):
            self.observed.update({key: payload[key] for key in ("run_id", "ae_pid", "module_base", "aex_sha256", "module", "module_filename") if key in payload})
            if kind in {"done", "complete", "finished"}:
                self.finished.set()


def _fixture_events(contract: dict[str, Any], explicit: Path | None, root: Path) -> list[Any]:
    source: Any = explicit
    if source is None:
        source = _first(contract, ("fixture_events",), ("fixture_events_path",), ("events_path",), ("parse_only", "events"))
    if isinstance(source, Path):
        path = source
        if not path.is_absolute():
            path = root / path
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if isinstance(source, str):
        path = Path(source)
        if not path.is_absolute():
            path = root / path
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if isinstance(source, list):
        return source
    raise RunnerError("--parse-only requires --events or contract fixture_events/events_path")


def _parse_fixture(values: list[Any]) -> tuple[list[dict[str, Any]], dict[str, Any], list[bytes]]:
    events: list[dict[str, Any]] = []
    identity: dict[str, Any] = {}
    chunks: list[bytes] = []
    for value in values:
        message = value if isinstance(value, dict) else {"payload": value}
        payload = message.get("payload", message)
        if isinstance(payload, dict) and str(payload.get("type", payload.get("kind", ""))).lower() in {"binary", "chunk", "bytes"}:
            data = payload.get("data", "")
            chunks.append(bytes.fromhex(data) if isinstance(data, str) and re.fullmatch(r"[0-9a-fA-F]*", data) else str(data).encode())
            continue
        event = _event_from_message(payload)
        if event:
            events.append(event)
            identity.update({key: event[key] for key in ("run_id", "ae_pid", "module_base", "aex_sha256", "renderer", "project_bpc", "module", "module_filename") if key in event})
    return events, identity, chunks


def _write_manifest(output: Path, manifest: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "result-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def _write_armed(capture: Capture, pid: int) -> dict[str, Any]:
    if not capture.observed.get("module_base"):
        raise RunnerError("agent configure returned without module identity")
    armed = {
        "schema_version": 1,
        "run_id": capture.contract["_runner"]["run_id"],
        "case_id": capture.case_id,
        "ae_pid": int(pid),
        "module": capture.contract["_runner"]["module"],
        "module_base": str(capture.observed["module_base"]),
        "aex_sha256": capture.contract["_runner"]["aex_sha256"],
        "renderer": capture.contract["_runner"]["renderer"],
        "project_bpc": capture.contract["_runner"]["project_bpc"],
    }
    capture.output.mkdir(parents=True, exist_ok=True)
    marker = capture.output / "armed.json"
    temporary = capture.output / ".armed.json.tmp"
    temporary.write_text(json.dumps(armed, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, marker)
    try:
        written = _json(marker)
    except RunnerError as exc:
        raise RunnerError(f"armed marker cannot be read back: {exc}") from exc
    if not isinstance(written, dict) or written != armed:
        raise RunnerError("armed marker is invalid or does not match the controller binding")
    return armed


def _finish(capture: Capture, status: str, error: str | None = None, identity: dict[str, Any] | None = None) -> int:
    capture.output.mkdir(parents=True, exist_ok=True)
    with (capture.output / "events.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for event in capture.events:
            stream.write(json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
    chunks = []
    for index, chunk in enumerate(capture.chunks, 1):
        path = capture.output / "chunks" / f"{index:06d}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(chunk["data"])
        chunks.append({"file": f"chunks/{path.name}", "index": index, "sha256": hashlib.sha256(chunk["data"]).hexdigest(), "size": len(chunk["data"]), "meta": chunk.get("meta", {})})
    manifest = {"schema_version": 1, "status": status, "run_id": capture.contract["_runner"]["run_id"], "module": capture.contract["_runner"]["module"], "aex_sha256": capture.contract["_runner"]["aex_sha256"], "events": len(capture.events), "chunks": chunks, "identity": identity or {}, "error": error or ""}
    _write_manifest(capture.output, manifest)
    if error:
        print(f"frida_runner: {error}", file=sys.stderr)
    return 0 if status == "answered" else 1


def run_parse_only(contract: dict[str, Any], output: Path, fixture: Path | None = None) -> int:
    known_pid = contract["_runner"].get("ae_pid")
    capture = Capture(contract, output, int(known_pid) if known_pid is not None else None,
                      contract["_runner"]["case_ids"][0] if len(contract["_runner"]["case_ids"]) == 1 else None)
    try:
        values = _fixture_events(contract, fixture, Path.cwd())
        for value in values:
            message = value if isinstance(value, dict) else {"payload": value}
            payload = message.get("payload", message)
            if isinstance(payload, str):
                try:
                    payload = _payload_object(payload)
                except RunnerError:
                    event = _event_from_message(payload)
                    if event:
                        capture.events.append(event)
                        capture.observed.update({key: event[key] for key in ("run_id", "ae_pid", "module_base", "aex_sha256", "renderer", "project_bpc", "module", "module_filename") if key in event})
                    continue
            if isinstance(payload, dict) and str(payload.get("event", payload.get("kind", payload.get("type", "")))).lower() in {"buffer", "binary", "chunk", "bytes"}:
                data = payload.get("data", message.get("data", b""))
                if isinstance(data, str) and re.fullmatch(r"[0-9a-fA-F]*", data):
                    data = bytes.fromhex(data)
                elif isinstance(data, str):
                    data = data.encode("latin1")
                if not isinstance(data, (bytes, bytearray)):
                    raise RunnerError("fixture binary event has no byte payload")
                capture.chunks.append({"data": bytes(data), "meta": payload})
                continue
            if isinstance(payload, dict) and str(payload.get("event", payload.get("kind", payload.get("type", "")))).lower() in {"module", "call", "return", "error", "agent_error", "exception"}:
                capture._record(payload)
            else:
                event = _event_from_message(payload)
                if event:
                    capture.events.append(event)
                    capture.observed.update({key: event[key] for key in ("run_id", "ae_pid", "module_base", "aex_sha256", "renderer", "project_bpc", "module", "module_filename") if key in event})
        identity = validate_capture(contract, capture.events, capture.observed, capture.pid, capture.case_id)
        return _finish(capture, "answered", identity=identity)
    except (RunnerError, OSError, ValueError) as exc:
        return _finish(capture, "failed", str(exc), capture.observed)


def _call_start(exports: Any, errors: list[BaseException]) -> None:
    try:
        exports.start()
    except BaseException as exc:  # propagate through the bounded worker
        errors.append(exc)


def run_live(
    contract: dict[str, Any],
    output: Path,
    pid: int | None,
    spawn: str | None,
    case_id: str | None = None,
    aex_path: str | None = None,
    completion_marker: Path | None = None,
) -> int:
    if case_id is None and len(contract["_runner"]["case_ids"]) == 1:
        case_id = contract["_runner"]["case_ids"][0]
    if case_id is not None and case_id not in contract["_runner"]["case_ids"]:
        raise RunnerError(f"unknown case id {case_id!r}")
    capture = Capture(contract, output, pid, case_id)
    session = script = device = None
    actual_pid = pid
    try:
        try:
            import frida  # type: ignore
        except ImportError as exc:
            raise RunnerError("Frida Python API is unavailable; use --parse-only for fixture validation") from exc
        device = frida.get_local_device()
        if pid is not None and spawn:
            raise RunnerError("--pid and --spawn are mutually exclusive")
        aex_path_value = aex_path or _first(contract, ("aex_path",), ("plugin", "aex_path"), ("plugin", "default_aex_path"))
        if aex_path_value:
            aex_path = Path(str(aex_path_value))
            if not aex_path.is_file():
                raise RunnerError(f"AEX path does not exist: {aex_path}")
            if _sha256(aex_path).lower() != contract["_runner"]["aex_sha256"]:
                raise RunnerError(f"AEX SHA-256 mismatch for {aex_path}")
        if spawn:
            actual_pid = int(device.spawn([spawn]))
        if actual_pid is None:
            contract_pid = _first(contract, ("pid",), ("identity", "ae_pid"))
            if contract_pid is None:
                raise RunnerError("live capture requires --pid or --spawn")
            actual_pid = int(contract_pid)
        session = device.attach(actual_pid)
        runner_dir = Path(__file__).resolve().parent
        agent_candidates = (runner_dir / "frida" / "agent.js", runner_dir.parent / "frida" / "agent.js")
        agent_path = next((candidate for candidate in agent_candidates if candidate.is_file()), agent_candidates[0])
        if not agent_path.is_file():
            raise RunnerError(f"Frida agent is missing: {agent_path}")
        script = session.create_script(agent_path.read_text(encoding="utf-8"))
        script.on("message", capture.message)
        script.load()
        config = dict(contract.get("agent", {}).get("config", {}) if isinstance(contract.get("agent"), dict) else {})
        transport = contract.get("transport", {})
        if isinstance(transport, dict) and isinstance(transport.get("agent_config"), dict):
            config.update(transport["agent_config"])
        hooks = contract.get("hooks", {})
        if isinstance(hooks, dict):
            config.setdefault("exports", hooks.get("entry", []))
            config.setdefault("internal_rvas", hooks.get("internal", []))
        config.update({"contract": contract, "run_id": contract["_runner"]["run_id"], "ae_pid": actual_pid,
                       "case_id": capture.case_id, "module_name": contract["_runner"]["module"],
                       "module_base": contract["_runner"].get("module_base"), "module_path": aex_path_value,
                       "aex_path": aex_path_value, "wait_timeout_ms": int(contract["_runner"]["timeout"] * 1000)})
        exports = getattr(script, "exports_sync", None)
        if exports is None or not hasattr(exports, "configure"):
            raise RunnerError("Frida agent does not expose configure")
        config["case_id"] = capture.case_id
        configure_result = exports.configure(config)
        if isinstance(configure_result, str):
            try:
                configure_result = _payload_object(configure_result)
            except RunnerError:
                configure_result = None
        if (not capture.observed.get("module_base") and isinstance(configure_result, dict)
                and isinstance(configure_result.get("module"), dict)):
            capture._record({"event": "module", "module": configure_result["module"], "ae_pid": actual_pid})
        if capture.error:
            raise RunnerError(capture.error)
        capture.observed.setdefault("ae_pid", actual_pid)
        _write_armed(capture, actual_pid)
        if spawn:
            device.resume(actual_pid)
        if exports is not None and hasattr(exports, "start"):
            start_error: list[BaseException] = []
            worker = threading.Thread(target=lambda: _call_start(exports, start_error), daemon=True)
            worker.start()
            worker.join(max(0.0, contract["_runner"]["timeout"] - (time.monotonic() - capture.started)))
            if worker.is_alive():
                raise RunnerError(f"capture timed out after {contract['_runner']['timeout']} seconds")
            if start_error:
                raise RunnerError(f"agent start failed: {start_error[0]}")
        deadline = time.monotonic() + contract["_runner"]["timeout"]
        if completion_marker is not None:
            while time.monotonic() < deadline and not completion_marker.is_file() and not capture.error:
                time.sleep(0.05)
            if not completion_marker.is_file():
                raise RunnerError(f"renderer completion marker was not observed before {contract['_runner']['timeout']} seconds")
        else:
            capture.finished.wait(max(0.0, deadline - time.monotonic()))
            if not capture.finished.is_set():
                raise RunnerError(f"capture timed out after {contract['_runner']['timeout']} seconds")
        if capture.error:
            raise RunnerError(capture.error)
        capture.observed.setdefault("ae_pid", actual_pid)
        identity = validate_capture(contract, capture.events, capture.observed, actual_pid, case_id)
        return _finish(capture, "answered", identity=identity)
    except (RunnerError, OSError, ValueError, TypeError) as exc:
        return _finish(capture, "failed", str(exc), capture.observed)
    finally:
        try:
            if script is not None:
                script.unload()
        finally:
            if session is not None:
                session.detach()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a fail-closed AfterFX Frida capture")
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pid", type=int)
    group.add_argument("--spawn", help="AfterFX executable path")
    parser.add_argument("--parse-only", action="store_true", help="validate fixture events without importing Frida")
    parser.add_argument("--events", type=Path, help="JSONL fixture path for --parse-only")
    parser.add_argument("--case-id", help="case to capture when the contract contains multiple cases")
    parser.add_argument("--run-id", help="runtime run identity generated by the PowerShell launcher")
    parser.add_argument("--module-base", help="pin the loaded module base")
    parser.add_argument("--aex-path", help="override the contract AEX path for SHA preflight")
    parser.add_argument("--completion-marker", type=Path, help="keep hooks armed until the AE launcher publishes this marker")
    args = parser.parse_args(argv)
    try:
        if not args.parse_only and (not args.run_id or not args.case_id):
            raise RunnerError("live capture requires --run-id and --case-id")
        contract = load_contract(args.contract, args.run_id)
        if args.module_base:
            contract["_runner"]["module_base"] = args.module_base
        if args.parse_only:
            return run_parse_only(contract, args.output_dir, args.events)
        return run_live(contract, args.output_dir, args.pid, args.spawn, args.case_id, args.aex_path, args.completion_marker)
    except (RunnerError, OSError) as exc:
        print(f"frida_runner: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
