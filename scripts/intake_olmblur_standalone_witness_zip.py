#!/usr/bin/env python3
"""Convert a standalone OLMBlur witness zip into repo-native conformance artifacts."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def load_witness(zip_path: Path) -> tuple[dict[str, Any], str | None]:
    with zipfile.ZipFile(zip_path) as zf:
        witness_name = next((name for name in zf.namelist() if name.endswith("WITNESS_RESULT.json")), None)
        if witness_name is None:
            raise FileNotFoundError("WITNESS_RESULT.json not found in zip")
        witness = json.loads(zf.read(witness_name).decode("utf-8"))
        readme_name = next((name for name in zf.namelist() if name.endswith("README_WITNESS.md")), None)
        readme = zf.read(readme_name).decode("utf-8", errors="replace") if readme_name else None
        return witness, readme


def output_paths(witness: dict[str, Any], args: argparse.Namespace) -> tuple[Path, Path]:
    target = witness["target"]
    stem = (
        f"olmblur_{witness['case']}_{witness['bit_depth']}_"
        f"{target['x']}_{target['y']}_{str(target['channel']).lower()}_witness_intake_20260630"
    ).replace("__", "_")
    out_json = args.output_json or ROOT / "refs" / "conformance" / f"{stem}.json"
    out_md = args.output_md or ROOT / "refs" / "conformance" / f"{stem}.md"
    return out_json, out_md


def build_payload(zip_path: Path, witness: dict[str, Any], readme: str | None) -> dict[str, Any]:
    decoded = witness.get("source_float_triplet_big_endian_decode", {})
    channel = str(witness["target"]["channel"]).lower()
    channel_value = decoded.get(channel)
    return {
        "kind": "olmblur_standalone_witness_intake",
        "source_zip": str(zip_path),
        "plugin": witness["plugin"],
        "case_id": witness["case"],
        "bit_depth": witness["bit_depth"],
        "target": witness["target"],
        "runtime_path": witness["runtime_path"],
        "registers_at_write": witness["registers_at_write"],
        "source_float_triplet_raw_words": witness["source_float_triplet_raw_words"],
        "source_float_triplet_big_endian_decode": decoded,
        "target_channel_pre_store_float": channel_value,
        "final_word": witness["final_word"],
        "interpretation": witness["interpretation"],
        "readme_excerpt": readme,
        "summary": (
            f"{witness['case']} {witness['bit_depth']} witness at "
            f"({witness['target']['x']},{witness['target']['y']}) channel {witness['target']['channel']} "
            f"shows pre-store {channel_value} -> final word {witness['final_word']['decimal']}."
        ),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OLMBlur Standalone Witness Intake",
        "",
        f"- Source zip: `{payload['source_zip']}`",
        f"- Case: `{payload['case_id']}`",
        f"- Bit depth: `{payload['bit_depth']}`",
        f"- Target: `{payload['target']}`",
        "",
        "## Summary",
        "",
        f"- {payload['summary']}",
        "",
        "## Runtime Path",
        "",
        f"- `{payload['runtime_path']}`",
        f"- Registers at write: `{payload['registers_at_write']}`",
        "",
        "## Float / Word Evidence",
        "",
        f"- Raw source words: `{payload['source_float_triplet_raw_words']}`",
        f"- Decoded source floats: `{payload['source_float_triplet_big_endian_decode']}`",
        f"- Target-channel pre-store float: `{payload['target_channel_pre_store_float']}`",
        f"- Final word: `{payload['final_word']}`",
        "",
        "## Interpretation",
        "",
        f"- {payload['interpretation']}",
    ]
    if payload.get("readme_excerpt"):
        lines.extend(["", "## Embedded README", "", payload["readme_excerpt"]])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    witness, readme = load_witness(args.source_zip)
    out_json, out_md = output_paths(witness, args)
    payload = build_payload(args.source_zip, witness, readme)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"output_json={out_json}")
    print(f"output_md={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
