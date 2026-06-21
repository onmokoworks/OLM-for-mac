#!/usr/bin/env python3
"""Generate a static OLM porting dashboard from local references and reports."""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "refs" / "reports" / "dashboard"

PLUGIN_ORDER = [
    "ColorKeep",
    "OLMBlur",
    "OLMColorKey",
    "OLMToonDilate",
    "OLMDistanceGradation",
    "OLMSmoother",
    "OLMSmoother2",
    "OLMDirectionalBlur",
    "OLMRadialBlur",
    "OLMKiraKira",
]

PLUGIN_ALIASES = [
    ("olmsmoother2", "OLMSmoother2"),
    ("olmsmootherv2", "OLMSmoother2"),
    ("smoother2", "OLMSmoother2"),
    ("smootherv2", "OLMSmoother2"),
    ("colorkeep", "ColorKeep"),
    ("olmblur", "OLMBlur"),
    ("olmcolorkey", "OLMColorKey"),
    ("olmtoondilate", "OLMToonDilate"),
    ("olmdistancegradation", "OLMDistanceGradation"),
    ("olmdirectionalblur", "OLMDirectionalBlur"),
    ("olmradialblur", "OLMRadialBlur"),
    ("olmkirakira", "OLMKiraKira"),
    ("olmsmoother", "OLMSmoother"),
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize_plugin(value: str | None) -> str:
    if not value:
        return "Unassigned"
    if value in PLUGIN_ORDER:
        return value
    compact = re.sub(r"[^a-z0-9]", "", value.lower())
    for key, plugin in PLUGIN_ALIASES:
        if key in compact:
            return plugin
    return "Unassigned"


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"_read_error": str(exc)}


def effect_names(case: dict) -> list[str]:
    names = []
    for effect in case.get("effects", []) or []:
        for key in ("match_name", "name"):
            value = effect.get(key)
            if value and value not in names:
                names.append(value)
    return names


def detect_engine(case: dict) -> str:
    text = " ".join(
        str(part)
        for part in [
            case.get("id", ""),
            case.get("frame", ""),
            case.get("project_gpu_accel_type", ""),
            case.get("gpu_accel_type", ""),
            case.get("renderer", ""),
        ]
    ).lower()
    if "software" in text:
        return "software"
    if "cuda" in text or "gpu" in text:
        return "cuda/gpu"
    return "unspecified"


def scan_manifests(reference_root: Path) -> tuple[dict, list[dict]]:
    by_plugin = defaultdict(list)
    manifests = []
    for path in sorted(reference_root.glob("**/reference_manifest.json")):
        data = read_json(path)
        cases = data.get("cases", []) if isinstance(data, dict) else []
        plugin = normalize_plugin(path.parent.name)
        if cases:
            detected = normalize_plugin(" ".join(effect_names(cases[0])))
            if detected != "Unassigned":
                plugin = detected
        engine_counts = defaultdict(int)
        effect_set = set()
        for case in cases:
            engine_counts[detect_engine(case)] += 1
            effect_set.update(effect_names(case))
        manifest = {
            "path": rel(path),
            "dir": rel(path.parent),
            "plugin": plugin,
            "case_count": len(cases),
            "engine_counts": dict(sorted(engine_counts.items())),
            "effects": sorted(effect_set),
            "created_at": data.get("created_at") if isinstance(data, dict) else None,
            "ae_version": data.get("ae_version") if isinstance(data, dict) else None,
        }
        manifests.append(manifest)
        by_plugin[plugin].append(manifest)
    return by_plugin, manifests


def load_neighbor_manifest(report_path: Path) -> dict | None:
    for parent in [report_path.parent.parent, report_path.parent.parent.parent, report_path.parent]:
        candidate = parent / "reference_manifest.json"
        if candidate.exists():
            data = read_json(candidate)
            if isinstance(data, dict) and "cases" in data:
                return data
    return None


def infer_report_plugin(report_path: Path, report: dict) -> str:
    manifest = load_neighbor_manifest(report_path)
    if manifest:
        cases = manifest.get("cases", [])
        if cases:
            return normalize_plugin(" ".join(effect_names(cases[0])))
    haystack = " ".join([rel(report_path), json.dumps(report.get("summary", {}), sort_keys=True)])
    return normalize_plugin(haystack)


def case_status(row: dict) -> str:
    status = row.get("status")
    if status == "compared":
        max_diff = row.get("max_diff")
        try:
            if int(max_diff) == 0:
                return "reported-exact"
            if int(max_diff) <= 1:
                return "off-by-1-candidate"
            return "diff"
        except (TypeError, ValueError):
            return "diff"
    if row.get("pass") is True:
        return "threshold-pass"
    if status:
        return str(status)
    return "unknown"


def scan_reports(report_roots: list[Path]) -> tuple[dict, list[dict]]:
    by_plugin = defaultdict(list)
    reports = []
    seen = set()
    for root in report_roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("**/*.json")):
            resolved = path.resolve()
            if resolved in seen or "dashboard" in path.parts:
                continue
            seen.add(resolved)
            report = read_json(path)
            if not isinstance(report, dict) or "cases" not in report:
                continue
            cases = report.get("cases") or []
            summary = report.get("summary") or {}
            plugin = infer_report_plugin(path, report)
            counts = defaultdict(int)
            max_diff = None
            mean_diff = None
            for row in cases:
                counts[case_status(row)] += 1
                if isinstance(row.get("max_diff"), (int, float)):
                    max_diff = row["max_diff"] if max_diff is None else max(max_diff, row["max_diff"])
                if isinstance(row.get("mean_diff"), (int, float)):
                    mean_diff = row["mean_diff"] if mean_diff is None else max(mean_diff, row["mean_diff"])
            item = {
                "path": rel(path),
                "plugin": plugin,
                "summary": summary,
                "case_count": len(cases),
                "counts": dict(sorted(counts.items())),
                "max_diff": max_diff,
                "max_mean_diff": mean_diff,
                "cases": [
                    {
                        "id": row.get("id", ""),
                        "frame": row.get("frame", ""),
                        "status": case_status(row),
                        "max_diff": row.get("max_diff"),
                        "mean_diff": row.get("mean_diff"),
                        "nonzero_px_percent": row.get("nonzero_px_percent"),
                    }
                    for row in cases
                ],
            }
            reports.append(item)
            by_plugin[plugin].append(item)
    return by_plugin, reports


def parse_progress_matrix(path: Path) -> dict:
    progress = defaultdict(lambda: {"measured": [], "estimate": None, "proof": "", "risk": "", "next": ""})
    if not path.exists():
        return progress
    lines = path.read_text(encoding="utf-8").splitlines()
    in_measured = False
    in_snapshot = False
    for line in lines:
        if line.startswith("| Plugin / path |"):
            in_measured = True
            in_snapshot = False
            continue
        if line.startswith("| Plugin | Estimate |"):
            in_snapshot = True
            in_measured = False
            continue
        if line.startswith("## ") and ("Measured" not in line and "Percent" not in line):
            in_measured = False
            in_snapshot = False
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if in_measured and len(cells) >= 2:
            plugin = normalize_plugin(cells[0])
            progress[plugin]["measured"].append({"path": cells[0], "result": cells[1]})
        elif in_snapshot and len(cells) >= 5:
            plugin = normalize_plugin(cells[0])
            match = re.search(r"(\d+)", cells[1])
            progress[plugin].update(
                {
                    "estimate": int(match.group(1)) if match else None,
                    "proof": cells[2],
                    "risk": cells[3],
                    "next": cells[4],
                }
            )
    return progress


def parse_markdown_table(lines: list[str], header_prefix: str) -> list[list[str]]:
    rows = []
    in_table = False
    for line in lines:
        if line.startswith(header_prefix):
            in_table = True
            continue
        if in_table and line.startswith("| ---"):
            continue
        if in_table and not line.startswith("|"):
            break
        if in_table:
            rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def parse_conformance_ledger(path: Path) -> dict:
    conformance = defaultdict(list)
    if not path.exists():
        return conformance
    lines = path.read_text(encoding="utf-8").splitlines()
    for cells in parse_markdown_table(lines, "| Plug-in / feature |"):
        if len(cells) < 6:
            continue
        feature, status_8bpc, status_16bpc, status_32bpc, evidence, next_proof = cells[:6]
        plugin = normalize_plugin(feature)
        conformance[plugin].append(
            {
                "feature": feature,
                "status_8bpc": status_8bpc,
                "status_16bpc": status_16bpc,
                "status_32bpc": status_32bpc,
                "evidence": evidence,
                "next_proof": next_proof,
            }
        )
    return conformance


def load_next_actions() -> dict:
    script = ROOT / "refs" / "scripts" / "next_reference_actions.py"
    if not script.exists():
        return {}
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--json"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return {"error": str(exc)}
    if proc.returncode != 0:
        return {"error": proc.stderr.strip() or f"exit {proc.returncode}"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"error": str(exc), "raw": proc.stdout[:1000]}


def latest_runtime_trace_package() -> dict:
    package_dir = ROOT / "refs" / "runtime_trace_packages"
    packages = sorted(package_dir.glob("*.zip"), key=lambda item: item.stat().st_mtime if item.exists() else 0)
    if not packages:
        return {"status": "missing", "dir": rel(package_dir)}
    latest = packages[-1]
    stat = latest.stat()
    return {
        "status": "ready",
        "relative_path": rel(latest),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds"),
        "mtime": stat.st_mtime,
    }


def latest_windows_batch() -> dict:
    batch_dir = ROOT / "handoffs" / "windows_batch"
    packages = sorted(batch_dir.glob("*.zip"), key=lambda item: item.stat().st_mtime if item.exists() else 0)
    if not packages:
        return {"status": "missing", "dir": rel(batch_dir)}
    latest = packages[-1]
    stat = latest.stat()
    return {
        "status": "ready",
        "relative_path": rel(latest),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds"),
        "mtime": stat.st_mtime,
    }


def latest_ae_pixel_validation_return() -> dict:
    returns_dir = ROOT / "handoffs" / "windows_returns"
    packages = []
    if returns_dir.exists():
        for path in returns_dir.glob("**/*.zip"):
            try:
                proc = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "list_olm_return_candidates.py"), "--json", str(path)],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                if proc.returncode != 0:
                    continue
                data = json.loads(proc.stdout)
            except (OSError, json.JSONDecodeError):
                continue
            rows = data.get("candidates", []) if isinstance(data, dict) else []
            if any(row.get("kind") == "ae-pixel-validation-return" for row in rows if isinstance(row, dict)):
                packages.append(path)
    if not packages:
        return {"status": "missing", "dir": rel(returns_dir)}
    latest = max(packages, key=lambda item: item.stat().st_mtime)
    stat = latest.stat()
    return {
        "status": "ready",
        "relative_path": rel(latest),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds"),
        "mtime": stat.st_mtime,
    }


def choose_send_target(runtime_package: dict, windows_batch: dict, ae_pixel_return: dict) -> dict:
    if (
        runtime_package.get("status") == "ready"
        and float(runtime_package.get("mtime", 0)) > float(windows_batch.get("mtime", 0))
    ):
        target = dict(runtime_package)
        target["kind"] = "runtime-trace-package"
        target["reason"] = "Newest handoff: a focused runtime trace package supersedes the older Windows action bundle."
        return target
    if (
        runtime_package.get("status") == "ready"
        and windows_batch.get("status") == "ready"
        and ae_pixel_return.get("status") == "ready"
        and float(ae_pixel_return.get("mtime", 0)) >= float(windows_batch.get("mtime", 0))
    ):
        target = dict(runtime_package)
        target["kind"] = "await-runtime-trace-return"
        target["reason"] = "The current Windows action bundle already returned AE pixel validation; remaining value is CDB/runtime trace."
        return target
    if windows_batch.get("status") == "ready":
        target = dict(windows_batch)
        target["kind"] = "windows-action-bundle"
        target["reason"] = "Preferred handoff: wraps the Smoother-first runtime trace plus AE-host validation requests."
        return target
    if runtime_package.get("status") == "ready":
        target = dict(runtime_package)
        target["kind"] = "runtime-trace-package"
        target["reason"] = "Fallback handoff: no Windows batch package was found."
        return target
    return {
        "status": "missing",
        "kind": "none",
        "reason": "No project-local Windows handoff package was found.",
    }


def audit_mediacore() -> dict:
    installer = ROOT / "scripts" / "install_mac_plugins_to_mediacore.sh"
    if not installer.exists():
        return {"status": "missing-installer"}
    try:
        proc = subprocess.run(
            [str(installer), "--audit-only"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as exc:
        return {"status": "error", "error": str(exc)}
    output = proc.stdout
    duplicate_count = output.count("[DUPLICATE]")
    missing_count = output.count("[MISS]")
    ok_count = output.count("[OK]")
    return {
        "status": "ok" if proc.returncode == 0 else "attention",
        "exit_code": proc.returncode,
        "ok_count": ok_count,
        "duplicate_count": duplicate_count,
        "missing_count": missing_count,
    }


def summarize_plugins(
    manifests_by_plugin: dict,
    reports_by_plugin: dict,
    progress: dict,
    conformance: dict,
    next_actions: dict,
) -> list[dict]:
    names = set(PLUGIN_ORDER) | set(manifests_by_plugin) | set(reports_by_plugin) | set(progress)
    names.discard("Unassigned")
    covered = next_actions.get("covered_actions", []) if isinstance(next_actions, dict) else []
    pending = next_actions.get("pending_actions", []) if isinstance(next_actions, dict) else []
    actions_by_plugin = defaultdict(lambda: {"covered": [], "pending": []})
    for kind, actions in [("covered", covered), ("pending", pending)]:
        for action in actions:
            plugin = normalize_plugin(" ".join([action.get("plugin_area", ""), action.get("effect", "")]))
            actions_by_plugin[plugin][kind].append(
                {
                    "request_id": action.get("request_id"),
                    "status": action.get("status"),
                    "command": action.get("command") or action.get("smoke_command"),
                    "reason": action.get("reason"),
                }
            )
    order = {name: index for index, name in enumerate(PLUGIN_ORDER)}
    plugins = []
    for name in sorted(names, key=lambda item: (order.get(item, 999), item)):
        manifests = manifests_by_plugin.get(name, [])
        reports = reports_by_plugin.get(name, [])
        case_counts = defaultdict(int)
        cli_exact = off_by_1 = threshold_pass = diff = missing = total_reported = 0
        max_diff = None
        for report in reports:
            counts = report.get("counts", {})
            cli_exact += counts.get("reported-exact", 0)
            off_by_1 += counts.get("off-by-1-candidate", 0)
            threshold_pass += counts.get("threshold-pass", 0)
            diff += counts.get("diff", 0)
            missing += counts.get("missing", 0)
            total_reported += report.get("case_count", 0)
            if isinstance(report.get("max_diff"), (int, float)):
                max_diff = report["max_diff"] if max_diff is None else max(max_diff, report["max_diff"])
        for manifest in manifests:
            for engine, count in manifest.get("engine_counts", {}).items():
                case_counts[engine] += count
        cli_exact_rate = round(100.0 * cli_exact / total_reported, 1) if total_reported else None
        plugins.append(
            {
                "name": name,
                "cli_exact_rate": cli_exact_rate,
                "manifest_count": len(manifests),
                "reference_cases": sum(item.get("case_count", 0) for item in manifests),
                "engine_counts": dict(sorted(case_counts.items())),
                "report_count": len(reports),
                "reported_cases": total_reported,
                "cli_exact_cases": cli_exact,
                "off_by_1_candidates": off_by_1,
                "threshold_pass_cases": threshold_pass,
                "diff_cases": diff,
                "missing_cases": missing,
                "max_diff": max_diff,
                "progress": dict(progress[name]) if name in progress else {"measured": []},
                "conformance": list(conformance.get(name, [])),
                "actions": dict(actions_by_plugin[name]),
                "manifests": manifests,
                "reports": reports,
            }
        )
    return plugins


def status_class(plugin: dict) -> str:
    rate = plugin.get("cli_exact_rate")
    if rate is not None:
        if rate == 100:
            return "good"
        if rate > 0:
            return "warn"
        return "bad"
    return "unknown"


def pct_label(plugin: dict) -> str:
    if plugin.get("cli_exact_rate") is not None:
        return f"{plugin['cli_exact_rate']:.1f}%"
    return "-"


def exact_count_label(plugin: dict) -> str:
    if plugin.get("reported_cases"):
        return f"{plugin['cli_exact_cases']}/{plugin['reported_cases']}"
    return "-"


def evidence_label(plugin: dict) -> str:
    rows = plugin.get("conformance", [])
    if not rows:
        return "ledgerなし"
    statuses = [row.get("status_8bpc", "unknown") for row in rows]
    if any("blocked" in status for status in statuses):
        return "blockedあり"
    if any("CLI residual" in status or "residual" in status for status in statuses):
        return "residualあり"
    if any("AE-host exact" in status for status in statuses):
        return "AE-host evidence"
    if any("CLI exact" in status for status in statuses):
        return "CLI exact evidence"
    if any("binary-grounded" in status for status in statuses):
        return "binary-grounded"
    if any("guarded" in status for status in statuses):
        return "guarded"
    return statuses[0]


def render_plugin_card(plugin: dict) -> str:
    measured = plugin.get("progress", {}).get("measured", [])[:8]
    measured_rows = "".join(
        f"<li><span>{escape(item['path'])}</span><b>{escape(item['result'])}</b></li>" for item in measured
    )
    if len(plugin.get("progress", {}).get("measured", [])) > len(measured):
        measured_rows += f"<li><span>more</span><b>{len(plugin['progress']['measured']) - len(measured)} rows</b></li>"
    if not measured_rows:
        measured_rows = "<li><span>No measured-bar note</span><b>-</b></li>"
    conformance_rows = "".join(
        "<li>"
        f"<span>{escape(item['feature'])}</span>"
        f"<b>{escape(item['status_8bpc'])}</b>"
        "</li>"
        for item in plugin.get("conformance", [])[:6]
    )
    if len(plugin.get("conformance", [])) > 6:
        conformance_rows += f"<li><span>more</span><b>{len(plugin['conformance']) - 6} rows</b></li>"
    if not conformance_rows:
        conformance_rows = "<li><span>No ledger row</span><b>-</b></li>"
    next_proof_rows = "".join(
        "<li>"
        f"<span>{escape(item['feature'])}</span>"
        f"<b>{escape(item['next_proof'])}</b>"
        "</li>"
        for item in plugin.get("conformance", [])[:4]
    )
    if not next_proof_rows:
        next_proof_rows = "<li><span>No ledger next proof</span><b>-</b></li>"
    action_rows = []
    for kind in ("covered", "pending"):
        for action in plugin.get("actions", {}).get(kind, []):
            action_rows.append(
                f"<li><span>{escape(kind)}: {escape(str(action.get('request_id') or '-'))}</span>"
                f"<b>{escape(str(action.get('status') or '-'))}</b></li>"
            )
    actions_html = "".join(action_rows) or "<li><span>No queued action</span><b>-</b></li>"
    manifest_html = "".join(
        f"<li><span>{escape(item['dir'])}</span><b>{item['case_count']} cases</b></li>"
        for item in plugin.get("manifests", [])[:6]
    )
    if not manifest_html:
        manifest_html = "<li><span>No local reference manifest</span><b>-</b></li>"
    engine_bits = ", ".join(f"{k}: {v}" for k, v in plugin.get("engine_counts", {}).items()) or "-"
    report_bits = (
        f"{plugin['cli_exact_cases']}/{plugin['reported_cases']} reported exact"
        if plugin.get("reported_cases")
        else "no durable diff report"
    )
    max_diff = plugin.get("max_diff")
    max_diff_html = str(max_diff) if max_diff is not None else "-"
    return f"""
    <section class="plugin-card {status_class(plugin)}" id="{escape(plugin['name'])}">
      <div class="card-head">
        <div>
          <h2>{escape(plugin['name'])}</h2>
          <p>{escape(evidence_label(plugin))} · {escape(report_bits)} · refs {plugin['reference_cases']}</p>
        </div>
        <div class="score" title="Durable report cases with max_diff=0. AE exact only when the report is an AE pixel validation report.">{exact_count_label(plugin)}</div>
      </div>
      <div class="metric-grid">
        <div><span>Reference cases</span><b>{plugin['reference_cases']}</b></div>
        <div><span>Engines</span><b>{escape(engine_bits)}</b></div>
        <div><span>Max diff</span><b>{escape(max_diff_html)}</b></div>
        <div><span>Non-exact / missing</span><b>{plugin['diff_cases'] + plugin['off_by_1_candidates'] + plugin['threshold_pass_cases']} / {plugin['missing_cases']}</b></div>
      </div>
      <div class="columns">
        <div>
          <h3>Conformance Ledger</h3>
          <ul>{conformance_rows}</ul>
        </div>
        <div>
          <h3>Next Required Proof</h3>
          <ul>{next_proof_rows}</ul>
        </div>
      </div>
      <details>
        <summary>Measured Notes / Queued Actions</summary>
        <div class="columns">
          <ul>{measured_rows}</ul>
          <ul>{actions_html}</ul>
        </div>
      </details>
      <details>
        <summary>Reference Manifests</summary>
        <ul>{manifest_html}</ul>
      </details>
    </section>
    """


def render_html(data: dict) -> str:
    plugins = data["plugins"]
    generated = escape(data["generated_at"])
    total_refs = sum(plugin["reference_cases"] for plugin in plugins)
    total_reported = sum(plugin["reported_cases"] for plugin in plugins)
    total_cli_exact = sum(plugin["cli_exact_cases"] for plugin in plugins)
    cli_exact_rate = round(100.0 * total_cli_exact / total_reported, 1) if total_reported else None
    card_html = "\n".join(render_plugin_card(plugin) for plugin in plugins)
    nav = "\n".join(f'<a href="#{escape(plugin["name"])}">{escape(plugin["name"])}</a>' for plugin in plugins)
    cli_exact_label = f"{cli_exact_rate:.1f}%" if cli_exact_rate is not None else "-"
    runtime_package = data.get("runtime_trace_package", {})
    windows_batch = data.get("windows_batch", {}) if isinstance(data.get("windows_batch"), dict) else {}
    send_target = data.get("send_target", {}) if isinstance(data.get("send_target"), dict) else {}
    policy = data.get("completion_policy", {}) if isinstance(data.get("completion_policy"), dict) else {}
    send_label = send_target.get("relative_path") or send_target.get("status", "-")
    send_detail = (
        f"{send_target.get('kind', '-')} · {send_target.get('size_bytes', 0)} bytes · {send_target.get('modified_at', '-')}"
        if send_target.get("status") == "ready"
        else str(send_target.get("reason", "not packaged"))
    )
    runtime_label = runtime_package.get("relative_path") or runtime_package.get("status", "-")
    runtime_detail = (
        f"{runtime_package.get('size_bytes', 0)} bytes · {runtime_package.get('modified_at', '-')}"
        if runtime_package.get("status") == "ready"
        else "not packaged"
    )
    batch_label = windows_batch.get("relative_path") or windows_batch.get("status", "-")
    batch_detail = (
        f"{windows_batch.get('size_bytes', 0)} bytes · {windows_batch.get('modified_at', '-')}"
        if windows_batch.get("status") == "ready"
        else "not packaged"
    )
    mediacore = data.get("mediacore_audit", {})
    mediacore_label = mediacore.get("status", "-")
    mediacore_detail = (
        f"ok={mediacore.get('ok_count', 0)} duplicate={mediacore.get('duplicate_count', 0)} missing={mediacore.get('missing_count', 0)}"
        if mediacore
        else "not checked"
    )
    next_actions = data.get("next_actions", {}) if isinstance(data.get("next_actions"), dict) else {}
    trace_actions = [
        action
        for action in next_actions.get("covered_actions", [])
        if action.get("status") == "runtime-trace" or action.get("mode") == "external-trace"
    ]
    trace_html = "".join(
        "<li>"
        f"<span>{escape(str(action.get('request_id') or '-'))}</span>"
        f"<b>{escape(str(action.get('plugin_area') or action.get('effect') or '-'))}</b>"
        "</li>"
        for action in trace_actions
    ) or "<li><span>No runtime trace action</span><b>-</b></li>"
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OLM Port Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #18202a;
      --muted: #687381;
      --line: #d9dee7;
      --good: #12805c;
      --warn: #9a6500;
      --bad: #b42318;
      --unknown: #5b6472;
      --accent: #2858a8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    header {{
      padding: 28px 32px 20px;
      border-bottom: 1px solid var(--line);
      background: #ffffff;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    header p {{ margin: 0; color: var(--muted); }}
    nav {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding: 12px 32px;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      position: sticky;
      top: 0;
      z-index: 2;
    }}
    nav a {{
      color: var(--accent);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 6px 9px;
      text-decoration: none;
      white-space: nowrap;
      font-size: 13px;
      background: #fbfcfe;
    }}
    main {{ max-width: 1440px; margin: 0 auto; padding: 22px 24px 44px; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(140px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .summary div, .ops-panel, .plugin-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .summary div {{ padding: 14px 16px; }}
    .summary span, .metric-grid span {{ display: block; color: var(--muted); font-size: 12px; }}
    .summary b {{ font-size: 24px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 14px;
    }}
    .ops-panel {{
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
      gap: 14px;
      padding: 16px;
      margin-bottom: 18px;
    }}
    .ops-panel h2 {{ font-size: 16px; margin-bottom: 6px; }}
    .ops-panel p {{ margin: 0 0 8px; color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }}
    .plugin-card {{ padding: 16px; border-top: 4px solid var(--unknown); }}
    .plugin-card.good {{ border-top-color: var(--good); }}
    .plugin-card.warn {{ border-top-color: var(--warn); }}
    .plugin-card.bad {{ border-top-color: var(--bad); }}
    .card-head {{ display: flex; justify-content: space-between; gap: 14px; align-items: start; }}
    h2 {{ margin: 0; font-size: 19px; letter-spacing: 0; }}
    h3 {{ margin: 16px 0 8px; font-size: 13px; color: var(--muted); letter-spacing: 0; }}
    .card-head p {{ margin: 3px 0 0; color: var(--muted); font-size: 13px; }}
    .score {{
      min-width: 74px;
      text-align: right;
      font-variant-numeric: tabular-nums;
      font-size: 25px;
      font-weight: 700;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 14px;
    }}
    .metric-grid div {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      min-height: 58px;
      overflow-wrap: anywhere;
    }}
    .metric-grid b {{ font-size: 14px; }}
    .columns {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    ul {{ list-style: none; margin: 0; padding: 0; }}
    li {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 7px 0;
      border-top: 1px solid #edf0f5;
      font-size: 12px;
    }}
    li span {{ color: var(--muted); overflow-wrap: anywhere; }}
    li b {{ text-align: right; overflow-wrap: anywhere; }}
    details {{ margin-top: 12px; }}
    summary {{ cursor: pointer; color: var(--accent); font-size: 13px; }}
    code {{ background: #edf0f5; padding: 2px 4px; border-radius: 4px; }}
    footer {{ color: var(--muted); font-size: 12px; margin-top: 20px; }}
    @media (max-width: 760px) {{
      header, nav {{ padding-left: 16px; padding-right: 16px; }}
      main {{ padding: 16px; }}
      .summary, .grid, .columns, .ops-panel {{ grid-template-columns: 1fr; }}
      .card-head {{ align-items: stretch; }}
      .score {{ font-size: 22px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>OLM Port Dashboard</h1>
    <p>Generated {generated}. Completion means AE exact; CLI exact is intermediate evidence only.</p>
  </header>
  <nav>{nav}</nav>
  <main>
    <section class="summary">
      <div><span>Plugins</span><b>{len(plugins)}</b></div>
      <div><span>Reference cases</span><b>{total_refs}</b></div>
      <div><span>Durable report cases</span><b>{total_reported}</b></div>
      <div><span>Reported exact cases</span><b>{total_cli_exact}</b></div>
    </section>
    <section class="ops-panel">
      <div>
        <h2>Completion Policy</h2>
        <p><code>{escape(str(policy.get('completion_status', 'AE exact')))}</code></p>
        <p>Reference: {escape(str(policy.get('reference_path', 'Windows AE Software render')))}</p>
        <p>Ledger: <code>{escape(str(policy.get('ledger', '-')))}</code></p>
        <p>IR index: <code>{escape(str(policy.get('ir_index', '-')))}</code></p>
      </div>
      <div>
        <h2>Next Send Target</h2>
        <p><code>{escape(str(send_label))}</code></p>
        <p>{escape(str(send_detail))}</p>
      </div>
      <div>
        <h2>Windows Batch Handoff</h2>
        <p><code>{escape(str(batch_label))}</code></p>
        <p>{escape(str(batch_detail))}</p>
      </div>
      <div>
        <h2>Runtime Trace Package</h2>
        <p><code>{escape(runtime_label)}</code></p>
        <p>{escape(runtime_detail)}</p>
      </div>
      <div>
        <h2>MediaCore Audit</h2>
        <p><code>{escape(str(mediacore_label))}</code></p>
        <p>{escape(mediacore_detail)}</p>
      </div>
      <div>
        <h2>Blocking External Trace Actions</h2>
        <ul>{trace_html}</ul>
      </div>
    </section>
    <section class="grid">{card_html}</section>
    <footer>
      Data file: <code>data.json</code>. Source notes: <code>notes/CONFORMANCE_LEDGER.md</code> and <code>notes/PROGRESS_MATRIX.md</code>.
      Source reports: <code>refs/reports/**/*.json</code> and <code>refs/runs/**/reports/*.json</code>.
    </footer>
  </main>
</body>
</html>
"""


def render_markdown(data: dict) -> str:
    plugins = data.get("plugins", [])
    total_refs = sum(plugin.get("reference_cases", 0) for plugin in plugins)
    total_reported = sum(plugin.get("reported_cases", 0) for plugin in plugins)
    total_cli_exact = sum(plugin.get("cli_exact_cases", 0) for plugin in plugins)

    runtime = data.get("runtime_trace_package", {}) if isinstance(data.get("runtime_trace_package"), dict) else {}
    windows_batch = data.get("windows_batch", {}) if isinstance(data.get("windows_batch"), dict) else {}
    send_target = data.get("send_target", {}) if isinstance(data.get("send_target"), dict) else {}
    policy = data.get("completion_policy", {}) if isinstance(data.get("completion_policy"), dict) else {}
    mediacore = data.get("mediacore_audit", {}) if isinstance(data.get("mediacore_audit"), dict) else {}
    next_actions = data.get("next_actions", {}) if isinstance(data.get("next_actions"), dict) else {}
    trace_actions = [
        action
        for action in next_actions.get("covered_actions", [])
        if action.get("status") == "runtime-trace" or action.get("mode") == "external-trace"
    ]

    lines = [
        "# OLM Port Dashboard",
        "",
        f"Generated: {data.get('generated_at', '-')}",
        "",
        "## Summary",
        "",
        "- Completion means AE exact. CLI exact is intermediate evidence only; reported exact just means max_diff=0 in the scanned report.",
        f"- Plugins: {len(plugins)}",
        f"- Reference cases: {total_refs}",
        f"- Durable report cases: {total_reported}",
        f"- Reported exact cases: {total_cli_exact}",
        "",
        "## Operations",
        "",
        f"- Completion status: {policy.get('completion_status', 'AE exact')}",
        f"- Reference path: {policy.get('reference_path', 'Windows AE Software render')}",
        f"- Conformance ledger: {policy.get('ledger', 'notes/CONFORMANCE_LEDGER.md')}",
        f"- IR index: {policy.get('ir_index', 'notes/IR_INDEX_20260621.md')}",
        f"- Next send target: {send_target.get('relative_path') or send_target.get('status', '-')}",
        f"- Next send target kind: {send_target.get('kind', '-')}",
        f"- Runtime trace package: {runtime.get('relative_path') or runtime.get('status', '-')}",
        f"- Runtime trace status: {runtime.get('status', '-')}",
        f"- Windows batch handoff: {windows_batch.get('relative_path') or windows_batch.get('status', '-')}",
        (
            "- MediaCore audit: "
            f"{mediacore.get('status', '-')} "
            f"(ok={mediacore.get('ok_count', 0)}, "
            f"duplicate={mediacore.get('duplicate_count', 0)}, "
            f"missing={mediacore.get('missing_count', 0)})"
        ),
        "",
        "## Blocking External Trace Actions",
        "",
    ]
    if trace_actions:
        for action in trace_actions:
            request_id = action.get("request_id") or "-"
            area = action.get("plugin_area") or action.get("effect") or "-"
            reason = action.get("reason") or action.get("mode") or action.get("status") or "-"
            lines.append(f"- {request_id}: {area} - {reason}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Plugins",
            "",
            "| Plugin | Evidence | Refs | Reports | Reported exact/Reported | Max diff | Next action |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for plugin in plugins:
        actions = []
        for kind in ("covered", "pending"):
            for action in plugin.get("actions", {}).get(kind, []):
                actions.append(f"{kind}:{action.get('request_id') or '-'}:{action.get('status') or '-'}")
        next_action = "<br>".join(actions[:3]) if actions else "-"
        max_diff = plugin.get("max_diff")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(plugin.get("name", "-")),
                    evidence_label(plugin),
                    str(plugin.get("reference_cases", 0)),
                    str(plugin.get("report_count", 0)),
                    f"{plugin.get('cli_exact_cases', 0)}/{plugin.get('reported_cases', 0)}",
                    str(max_diff if max_diff is not None else "-"),
                    next_action,
                ]
            )
            + " |"
        )

    lines.append("")
    return "\n".join(lines)


def build_data(args: argparse.Namespace) -> dict:
    reference_root = ROOT / "refs" / "win_references"
    report_roots = [ROOT / "refs" / "reports", ROOT / "refs" / "runs"]
    if args.scan_tmp:
        report_roots.extend(Path("/tmp").glob("**/reports"))
    manifests_by_plugin, manifests = scan_manifests(reference_root)
    reports_by_plugin, reports = scan_reports(report_roots)
    progress = parse_progress_matrix(ROOT / "notes" / "PROGRESS_MATRIX.md")
    conformance = parse_conformance_ledger(ROOT / "notes" / "CONFORMANCE_LEDGER.md")
    next_actions = load_next_actions()
    plugins = summarize_plugins(manifests_by_plugin, reports_by_plugin, progress, conformance, next_actions)
    runtime_package = latest_runtime_trace_package()
    windows_batch = latest_windows_batch()
    ae_pixel_return = latest_ae_pixel_validation_return()
    return {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "root": ROOT.name,
        "completion_policy": {
            "completion_status": "AE exact",
            "reference_path": "Windows AE Software render",
            "gpu_scope": "excluded from current exactness claims",
            "bit_depth_order": ["8bpc", "16bpc", "32bpc"],
            "policy_note": rel(ROOT / "notes" / "AE_EXACT_CONFORMANCE.md"),
            "ledger": rel(ROOT / "notes" / "CONFORMANCE_LEDGER.md"),
            "ir_index": rel(ROOT / "notes" / "IR_INDEX_20260621.md"),
            "ir_template": rel(ROOT / "notes" / "BINARY_GROUNDED_IR_TEMPLATE.md"),
            "bit_depth_strategy": rel(ROOT / "notes" / "BIT_DEPTH_REFERENCE_STRATEGY.md"),
        },
        "plugins": plugins,
        "manifests": manifests,
        "reports": reports,
        "unassigned_reports": reports_by_plugin.get("Unassigned", []),
        "next_actions": next_actions,
        "send_target": choose_send_target(runtime_package, windows_batch, ae_pixel_return),
        "runtime_trace_package": runtime_package,
        "windows_batch": windows_batch,
        "ae_pixel_validation_return": ae_pixel_return,
        "mediacore_audit": audit_mediacore(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--markdown",
        type=Path,
        default=None,
        help="Also write a Markdown summary for terminal/Finder handoff workflows.",
    )
    parser.add_argument(
        "--scan-tmp",
        action="store_true",
        help="Also scan /tmp/**/reports/*.json. Useful for ad-hoc smoke runs, but not reproducible.",
    )
    args = parser.parse_args()
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    data = build_data(args)
    (out_dir / "data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "index.html").write_text(render_html(data), encoding="utf-8")
    if args.markdown:
        markdown_path = args.markdown.resolve()
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown(data), encoding="utf-8")
        print(f"dashboard_markdown={markdown_path}")
    print(f"dashboard_html={out_dir / 'index.html'}")
    print(f"dashboard_data={out_dir / 'data.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
