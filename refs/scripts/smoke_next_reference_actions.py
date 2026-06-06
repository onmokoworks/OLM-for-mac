#!/usr/bin/env python3
"""Smoke-test next_reference_actions.py pending and covered outputs."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )


def main() -> int:
    root = repo_root()
    script = root / "refs" / "scripts" / "next_reference_actions.py"
    with tempfile.TemporaryDirectory(prefix="olm_next_ref_action_smoke_") as tmp:
        tmpdir = Path(tmp)
        requests = tmpdir / "requests"
        references = tmpdir / "references"
        shutil.copytree(root / "refs" / "reference_requests", requests)
        references.mkdir()

        pending = run(
            [
                sys.executable,
                str(script),
                "--requests",
                str(requests),
                "--references",
                str(references),
                "--json",
            ],
            root,
            capture=True,
        )
        pending_doc = json.loads(pending.stdout)
        assert pending_doc["next_action"] is None
        assert "smoother2_no_key_grid_20260606" in pending_doc["pending"]
        pending_actions = pending_doc["pending_actions"]
        assert pending_actions[0]["request_id"] == "smoother2_no_key_grid_20260606"
        assert pending_actions[0]["status"] == "pending"
        assert pending_actions[0]["write_scope"] == "none"
        assert pending_actions[0]["unblock_request"] == "smoother2_no_key_grid_20260606"
        assert "notes/SUBAGENT_ASSIGNMENTS.md" in pending_actions[0]["prior_audit_refs"]
        assert "notes/PARALLEL_IR_AUDIT_20260606.md" in pending_actions[0]["agent_prompt"]
        assert "stop before PNG-only implementation tuning" in pending_actions[0]["stop_condition"]
        assert "Pending reference request" in pending_actions[0]["agent_prompt"]
        assert "do not tune from current PNG residuals" in pending_actions[0]["agent_prompt"]
        assert "avoid restating old audits" in pending_actions[0]["agent_prompt"]
        assert "Workspace: /Users/onmk/Documents/Projects/Personal/OLM as" in pending_actions[0]["copy_paste_prompt"]
        assert "First run or inspect:" in pending_actions[0]["copy_paste_prompt"]
        directional = next(action for action in pending_actions if action["request_id"] == "directionalblur_context_scale_20260606")
        assert "refs/scripts/smoke_olmdirectionalblur*.py" in directional["copy_paste_prompt"]
        assert "refs/scripts/smoke_olmdirectionalblur_cpp_cli.py" not in directional["copy_paste_prompt"]
        assert "refs/scripts/smoke_olmdirectionalblur_cpp_cli.py" in directional["read_files_resolved"]
        assert directional["read_file_patterns"] == ["refs/scripts/smoke_olmdirectionalblur*.py"]

        dispatch_dir = tmpdir / "dispatch"
        run(
            [
                sys.executable,
                str(script),
                "--requests",
                str(requests),
                "--references",
                str(references),
                "--json",
                "--dispatch-dir",
                str(dispatch_dir),
            ],
            root,
            capture=True,
        )
        assert (dispatch_dir / "index.json").exists()
        pending_md = dispatch_dir / "pending" / "01_smoother2_no_key_grid_20260606" / "SUBAGENT.md"
        assert pending_md.exists()
        assert "OLMSmoother2 no-key" in pending_md.read_text(encoding="utf-8")
        assert (dispatch_dir / "pending" / "01_smoother2_no_key_grid_20260606" / "action.json").exists()

        pending_human = run(
            [
                sys.executable,
                str(script),
                "--requests",
                str(requests),
                "--references",
                str(references),
            ],
            root,
            capture=True,
        )
        assert "next pending subagent" in pending_human.stdout
        assert "- request: smoother2_no_key_grid_20260606" in pending_human.stdout
        assert "stop before PNG-only implementation tuning" in pending_human.stdout
        assert "smoke_olmsmoother2_no_key_grid_cli.py" in pending_human.stdout

        source = tmpdir / "returned"
        effect_dir = source / "OLMSmoother2"
        effect_dir.mkdir(parents=True)
        manifest = {
            "kind": "ae_effect_reference_manifest",
            "effect": {"name": "OLM Smoother v2"},
            "render_set": "software",
            "project_gpu_accel_type": {"current_name": "SOFTWARE"},
            "cases": [],
        }
        request = json.loads((requests / "smoother2_no_key_grid_20260606.json").read_text(encoding="utf-8"))
        for case in request["cases"]:
            before = f"{case['id']}_before.png"
            after = f"{case['id']}.png"
            (effect_dir / before).write_bytes(b"\x89PNG\r\n\x1a\n")
            (effect_dir / after).write_bytes(b"\x89PNG\r\n\x1a\n")
            manifest["cases"].append(
                {
                    "id": f"SOFTWARE_{case['id']}",
                    "request_case_id": case["id"],
                    "frame": after,
                    "before_effects_frame": before,
                    "params": dict(case.get("params", {})),
                    "render_set": "software",
                    "project_gpu_accel_type": {"current_name": "SOFTWARE"},
                }
            )
        (effect_dir / "reference_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        covered = run(
            [
                sys.executable,
                str(script),
                "--requests",
                str(requests),
                "--references",
                str(references),
                "--json",
            ],
            root,
            capture=True,
        )
        # First call should still be pending because the synthetic source was not imported.
        assert json.loads(covered.stdout)["next_action"] is None

        imported = references / "synthetic_return"
        shutil.copytree(source, imported)
        covered = run(
            [
                sys.executable,
                str(script),
                "--requests",
                str(requests),
                "--references",
                str(references),
                "--json",
            ],
            root,
            capture=True,
        )
        covered_doc = json.loads(covered.stdout)
        action = covered_doc["next_action"]
        assert action["request_id"] == "smoother2_no_key_grid_20260606"
        assert action["plugin_area"] == "OLMSmoother2 no-key"
        assert action["mode"] == "explorer"
        assert action["write_scope"] == "none"
        assert "notes/OLMSmoother2_ASM_FACTS.md" in action["read_files"]
        assert "smoke_olmsmoother2_no_key_grid_cli.py" in action["command"]
        assert action["smoke_command"] == action["command"]
        assert action["unblock_request"] == "smoother2_no_key_grid_20260606"
        assert "run the request smoke" in action["stop_condition"]
        assert "First run or inspect:" in action["agent_prompt"]
        assert "Do not edit" in action["agent_prompt"]
        assert "copy_paste_prompt" in action
        assert covered_doc["pending_actions"][0]["request_id"] == "olmcolorkey_replace_colorspace_20260606"

    print("[OK] next reference actions smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
