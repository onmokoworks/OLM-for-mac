"""Validation and deterministic archive helpers for Windows witness specs."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
PLACEHOLDER_RE = re.compile(r"\{\{([^{}]+)\}\}")
STATIC_PLACEHOLDERS = {
    "RUN_ID",
    "AE_PID",
    "MODULE_BASE",
    "AEX_SHA256",
    "PROJECT_BPC",
    "RENDERER",
    "CASE_ID",
    "TRACE_PATH",
    "ARTIFACT_PATH",
}
DRIVE_PATH_RE = re.compile(r"^[A-Za-z]:")


class SpecError(ValueError):
    """Raised when a witness spec cannot be compiled safely."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise SpecError(message)


def _keys(value: Any, required: set[str], allowed: set[str], where: str) -> None:
    _need(isinstance(value, dict), f"{where} must be an object")
    missing = sorted(required - set(value))
    extra = sorted(set(value) - allowed)
    _need(not missing, f"{where} missing keys: {', '.join(missing)}")
    _need(not extra, f"{where} has unknown keys: {', '.join(extra)}")


def _relative_parts(value: str, where: str) -> list[str]:
    _need(isinstance(value, str) and bool(value), f"{where} must be a non-empty relative path")
    _need("\\" not in value, f"{where} may not contain backslashes")
    _need(not value.startswith("/"), f"{where} must be a relative path")
    _need(DRIVE_PATH_RE.match(value) is None, f"{where} may not be a drive path")
    parts = value.split("/")
    for part in parts:
        _need(part not in ("", ".", ".."), f"{where} has unsafe path component {part!r}")
    return parts


def _safe_relative(value: str, where: str) -> None:
    _relative_parts(value, where)


def _safe_filename(value: str, where: str) -> None:
    parts = _relative_parts(value, where)
    _need(len(parts) == 1, f"{where} must be a filename")


def _expand_case_path(value: str, case_id: str) -> str:
    return value.replace("{case_id}", case_id)


def _archive_key(value: str) -> str:
    return "/".join(part.casefold() for part in _relative_parts(value, "archive path"))


def _check_archive_collision(
    seen: dict[str, tuple[str, str]],
    archive_path: str,
    where: str,
) -> None:
    _relative_parts(archive_path, f"{where} archive path")
    key = _archive_key(archive_path)
    previous = seen.get(key)
    if previous is not None:
        previous_where, previous_path = previous
        raise SpecError(
            f"{where} archive path {archive_path!r} collides with "
            f"{previous_where} archive path {previous_path!r}"
        )
    seen[key] = (where, archive_path)


def validate_template(text: str, values: dict[str, Any], addresses: dict[str, str], where: str) -> None:
    _need(
        re.search(r"(?mi)^\s*\.logopen\s+/t\s+\"?\{\{TRACE_PATH\}\}\"?\s*$", text) is not None,
        f"{where} must use `.logopen /t \"{{{{TRACE_PATH}}}}\"` to truncate stale traces",
    )
    for placeholder in PLACEHOLDER_RE.findall(text):
        if placeholder in STATIC_PLACEHOLDERS:
            continue
        if placeholder.startswith("CASE_VALUE:") and placeholder[11:] in values:
            continue
        if placeholder.startswith("ADDRESS:") and placeholder[8:] in addresses:
            continue
        raise SpecError(f"{where} has unsupported placeholder {{{{{placeholder}}}}}")


def validate_spec(spec: dict[str, Any], base_dir: Path | None = None) -> None:
    """Validate the M0 subset without requiring the external jsonschema package."""

    root_required = {
        "schema_version", "request_id", "run_id_prefix", "plugin", "host", "project",
        "renderer", "request_assets", "cdb", "cases", "validation", "return_bundle",
    }
    _keys(spec, root_required, root_required | {"description"}, "spec")
    _need(spec["schema_version"] == SCHEMA_VERSION, "schema_version must be 1")
    for key in ("request_id", "run_id_prefix"):
        _need(isinstance(spec[key], str) and ID_RE.fullmatch(spec[key]) is not None, f"{key} is invalid")

    plugin = spec["plugin"]
    _keys(plugin, {"name", "module_filename", "aex_sha256", "default_aex_path"},
          {"name", "module_filename", "aex_sha256", "default_aex_path"}, "plugin")
    _need(isinstance(plugin["name"], str) and bool(plugin["name"]), "plugin.name is required")
    _need(Path(plugin["module_filename"]).name == plugin["module_filename"], "plugin.module_filename must be a filename")
    _need(SHA256_RE.fullmatch(plugin["aex_sha256"]) is not None, "plugin.aex_sha256 must be lowercase SHA-256")

    host = spec["host"]
    _keys(host, {"afterfx_path", "cdb_path"}, {"afterfx_path", "cdb_path"}, "host")
    project = spec["project"]
    _keys(project, {"bits_per_channel", "renderer"}, {"bits_per_channel", "renderer", "environment"}, "project")
    _need(project["bits_per_channel"] in (8, 16, 32), "project.bits_per_channel must be 8, 16, or 32")
    _need(project["renderer"] == "Software", "M0 requires project.renderer=Software")
    environment = project.get("environment", {})
    _need(isinstance(environment, dict), "project.environment must be an object")
    for name, value in environment.items():
        _need(re.fullmatch(r"[A-Z][A-Z0-9_]*", name) is not None, f"invalid environment name: {name}")
        _need(isinstance(value, str), f"project.environment.{name} must be a string")

    renderer = spec["renderer"]
    _keys(renderer, {"source"}, {"source"}, "renderer")
    _safe_relative(renderer["source"], "renderer.source")
    assets = spec["request_assets"]
    _keys(assets, {"source"}, {"source"}, "request_assets")
    _safe_relative(assets["source"], "request_assets.source")

    cdb = spec["cdb"]
    _keys(cdb, {"armed_marker", "arm_timeout_seconds", "capture_timeout_seconds"},
          {"armed_marker", "arm_timeout_seconds", "capture_timeout_seconds"}, "cdb")
    _need(isinstance(cdb["armed_marker"], str) and bool(cdb["armed_marker"]), "cdb.armed_marker is required")
    for key in ("arm_timeout_seconds", "capture_timeout_seconds"):
        _need(isinstance(cdb[key], int) and cdb[key] > 0, f"cdb.{key} must be a positive integer")

    cases = spec["cases"]
    _need(isinstance(cases, list) and cases, "cases must be a non-empty array")
    seen_cases: set[str] = set()
    for index, case in enumerate(cases):
        where = f"cases[{index}]"
        _keys(case, {"id", "cdb_template"}, {"id", "cdb_template", "template_values", "addresses", "exports"}, where)
        _need(isinstance(case["id"], str) and ID_RE.fullmatch(case["id"]) is not None, f"{where}.id is invalid")
        _need(case["id"] not in seen_cases, f"duplicate case id: {case['id']}")
        seen_cases.add(case["id"])
        _safe_relative(case["cdb_template"], f"{where}.cdb_template")
        values = case.get("template_values", {})
        addresses = case.get("addresses", {})
        _need(isinstance(values, dict), f"{where}.template_values must be an object")
        _need(isinstance(addresses, dict), f"{where}.addresses must be an object")
        for name, rva in addresses.items():
            _need(ID_RE.fullmatch(name) is not None, f"{where}.addresses key is invalid: {name}")
            _need(isinstance(rva, str) and re.fullmatch(r"0x[0-9a-fA-F]+", rva) is not None,
                  f"{where}.addresses.{name} must be a hexadecimal RVA")
        exports = case.get("exports", [])
        _need(isinstance(exports, list), f"{where}.exports must be an array")
        for export_index, export in enumerate(exports):
            export_where = f"{where}.exports[{export_index}]"
            _keys(export, {"source", "archive_path", "required"}, {"source", "archive_path", "required"}, export_where)
            _safe_relative(export["source"], f"{export_where}.source")
            _safe_relative(export["archive_path"], f"{export_where}.archive_path")
            _need(isinstance(export["required"], bool), f"{export_where}.required must be boolean")
        if base_dir is not None:
            template_path = base_dir / case["cdb_template"]
            _need(template_path.is_file(), f"missing CDB template: {template_path}")
            validate_template(template_path.read_text(encoding="utf-8"), values, addresses, str(template_path))

    validation = spec["validation"]
    _keys(validation, {"identity_fields", "events"}, {"identity_fields", "events"}, "validation")
    identity = validation["identity_fields"]
    _need(isinstance(identity, list) and identity, "validation.identity_fields must be a non-empty array")
    _need(len(identity) == len(set(identity)), "validation.identity_fields contains duplicates")
    required_identity = {"run_id", "ae_pid", "module_base", "aex_sha256", "project_bpc", "renderer", "case_id"}
    _need(required_identity <= set(identity), "validation.identity_fields lacks common run identity fields")
    events = validation["events"]
    _need(isinstance(events, list) and events, "validation.events must be a non-empty array")
    seen_prefixes: set[str] = set()
    for index, event in enumerate(events):
        where = f"validation.events[{index}]"
        _keys(event, {"name", "prefix", "cardinality", "required_fields"},
              {"name", "prefix", "cardinality", "required_fields", "field_constraints", "field_relations"}, where)
        _need(ID_RE.fullmatch(event["name"]) is not None, f"{where}.name is invalid")
        _need(re.fullmatch(r"[A-Z][A-Z0-9_]*", event["prefix"]) is not None, f"{where}.prefix is invalid")
        _need(event["prefix"] not in seen_prefixes, f"duplicate event prefix: {event['prefix']}")
        seen_prefixes.add(event["prefix"])
        card = event["cardinality"]
        _keys(card, {"scope", "min", "max"}, {"scope", "min", "max"}, f"{where}.cardinality")
        _need(card["scope"] in ("per_case", "global"), f"{where}.cardinality.scope is invalid")
        _need(isinstance(card["min"], int) and isinstance(card["max"], int) and 0 <= card["min"] <= card["max"],
              f"{where}.cardinality requires 0 <= min <= max")
        fields = event["required_fields"]
        _need(isinstance(fields, list) and len(fields) == len(set(fields)), f"{where}.required_fields must be unique")
        _need(set(identity) <= set(fields), f"{where}.required_fields must include all identity_fields")
        constraints = event.get("field_constraints", {})
        _need(isinstance(constraints, dict), f"{where}.field_constraints must be an object")
        for field, constraint in constraints.items():
            _keys(constraint, set(), {"equals", "pattern"}, f"{where}.field_constraints.{field}")
            _need(bool(constraint), f"{where}.field_constraints.{field} may not be empty")
            if "pattern" in constraint:
                try:
                    re.compile(constraint["pattern"])
                except re.error as exc:
                    raise SpecError(f"{where}.field_constraints.{field}.pattern is invalid: {exc}") from exc
        relations = event.get("field_relations", [])
        _need(isinstance(relations, list), f"{where}.field_relations must be an array")
        relation_fields = {
            "address_field", "base_field", "row_field", "row_origin_field",
            "column_field", "column_origin_field", "stride_field",
        }
        seen_relation_targets: set[str] = set()
        for relation_index, relation in enumerate(relations):
            relation_where = f"{where}.field_relations[{relation_index}]"
            required = {"type", *relation_fields, "element_size", "channel_offset"}
            _keys(relation, required, required, relation_where)
            _need(relation["type"] == "address_arithmetic", f"{relation_where}.type is invalid")
            for key in relation_fields:
                field = relation[key]
                _need(isinstance(field, str) and ID_RE.fullmatch(field) is not None,
                      f"{relation_where}.{key} is invalid")
                _need(field in fields, f"{relation_where}.{key} must name a required field")
            target = relation["address_field"]
            _need(target not in seen_relation_targets,
                  f"{relation_where}.address_field duplicates relation target {target}")
            seen_relation_targets.add(target)
            _need(type(relation["element_size"]) is int and relation["element_size"] > 0,
                  f"{relation_where}.element_size must be a positive integer")
            _need(type(relation["channel_offset"]) is int and relation["channel_offset"] >= 0,
                  f"{relation_where}.channel_offset must be a nonnegative integer")

    bundle = spec["return_bundle"]
    _keys(bundle, {"json_name", "zip_name"}, {"json_name", "zip_name", "include_logs"}, "return_bundle")
    for key in ("json_name", "zip_name"):
        _safe_filename(bundle[key], f"return_bundle.{key}")
    logs = bundle.get("include_logs", [])
    _need(isinstance(logs, list), "return_bundle.include_logs must be an array")
    archive_entries: dict[str, tuple[str, str]] = {}
    _check_archive_collision(archive_entries, bundle["json_name"], "return_bundle.json_name")
    for index, path in enumerate(logs):
        _safe_relative(path, f"return_bundle.include_logs[{index}]")
        _check_archive_collision(
            archive_entries,
            f"logs/{path}",
            f"return_bundle.include_logs[{index}]",
        )
    for case_index, case in enumerate(cases):
        for export_index, export in enumerate(case.get("exports", [])):
            _check_archive_collision(
                archive_entries,
                _expand_case_path(export["archive_path"], case["id"]),
                f"cases[{case_index}].exports[{export_index}].archive_path",
            )

    if base_dir is not None:
        _need((base_dir / renderer["source"]).is_file(), f"missing renderer source: {base_dir / renderer['source']}")
        request_assets_dir = base_dir / assets["source"]
        _need(request_assets_dir.is_dir(), f"missing request assets: {request_assets_dir}")
        request_manifest = request_assets_dir / "request_manifest.json"
        if request_manifest.is_file():
            try:
                embedded = json.loads(request_manifest.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as exc:
                raise SpecError(f"could not read embedded request manifest {request_manifest}: {exc}") from exc
            _need(isinstance(embedded, dict), f"{request_manifest} must be a JSON object")
            _need(
                isinstance(embedded.get("request_id"), str) and bool(embedded["request_id"]),
                f"{request_manifest} must define request_id",
            )
            _need(
                embedded["request_id"] == spec["request_id"],
                f"{request_manifest} request_id must exactly match spec.request_id",
            )


def load_spec(path: Path) -> dict[str, Any]:
    path = path.resolve()
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecError(f"could not read spec {path}: {exc}") from exc
    validate_spec(spec, path.parent)
    return spec


def canonical_json(data: Any) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def deterministic_zip(root: Path, output: Path, files: Iterable[Path] | None = None) -> None:
    selected = sorted(files or (path for path in root.rglob("*") if path.is_file()), key=lambda path: path.relative_to(root).as_posix())
    archive_entries: dict[str, tuple[str, str]] = {}
    named_files: list[tuple[Path, str]] = []
    for path in selected:
        name = path.relative_to(root).as_posix()
        _check_archive_collision(archive_entries, name, str(path.relative_to(root)))
        named_files.append((path, name))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, name in named_files:
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
