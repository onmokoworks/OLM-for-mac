from __future__ import annotations

import ast
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools" / "emulation"
REFS_DIR = REPO_ROOT / "refs" / "conformance"

M4_REPORT = TOOLS_DIR / "M4_REPORT.md"
M5_JSON = TOOLS_DIR / "M5_CELL_WRITES.json"
OUT_JSON = REFS_DIR / "olmradialblur_static_witness_20260708.json"
OUT_MD = REFS_DIR / "olmradialblur_static_witness_20260708.md"


def repo_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def require_match(pattern: str, text: str, label: str) -> re.Match[str]:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise RuntimeError(f"could not find {label} in {M4_REPORT}")
    return match


def tuple_from_group(match: re.Match[str], group_index: int) -> tuple:
    return ast.literal_eval(match.group(group_index))


def load_m4_summary() -> dict:
    text = M4_REPORT.read_text(encoding="utf-8")

    buffers = require_match(
        r"witness buffers: `f250=(0x[0-9a-f]+)`, `f252=(0x[0-9a-f]+)`, `\+0xe=(0x[0-9a-f]+)`",
        text,
        "witness buffers",
    )
    output = require_match(
        r"output witness `\(1614,6\)` ARGB bytes `(\([^`]+\))`, RGBA `(\([^`]+\))`",
        text,
        "output witness",
    )
    direct = require_match(
        r"direct inverse sample `\(1614,6\)`: radius=([0-9.\-]+), angle=([0-9.\-]+), "
        r"angle_scale=([0-9.\-]+), radius_base=([0-9\-]+), sample=\(([0-9.\-]+), ([0-9.\-]+)\), "
        r"`\+0xe` RGBA float=(\([^`]+\)), u8=(\([^`]+\))",
        text,
        "direct inverse sample",
    )
    extra = re.findall(
        r"row(\d+) col(\d+): \+0xe bits `([0-9a-f ]+)`, f250=(\([^`]+\))",
        text,
        flags=re.MULTILINE,
    )

    extra_cells: dict[str, dict] = {}
    for row_s, col_s, bits, f250 in extra:
        key = f"row{row_s}_col{col_s}"
        extra_cells[key] = {
            "e0e_bits": bits.split(),
            "f250": list(ast.literal_eval(f250)),
        }

    return {
        "buffers": {
            "f250": buffers.group(1),
            "f252": buffers.group(2),
            "e0e": buffers.group(3),
        },
        "output_witness": {
            "argb_bytes": list(tuple_from_group(output, 1)),
            "rgba_bytes": list(tuple_from_group(output, 2)),
        },
        "direct_inverse_sample": {
            "radius": float(direct.group(1)),
            "angle": float(direct.group(2)),
            "angle_scale": float(direct.group(3)),
            "radius_base": int(direct.group(4)),
            "sample_x": float(direct.group(5)),
            "sample_y": float(direct.group(6)),
            "e0e_rgba_float": list(tuple_from_group(direct, 7)),
            "u8": list(tuple_from_group(direct, 8)),
        },
        "extra_cells": extra_cells,
    }


def load_m5_summary() -> dict:
    data = json.loads(M5_JSON.read_text(encoding="utf-8"))
    return {
        "elapsed_seconds": data["elapsed_seconds"],
        "angular_cols": data["angular_cols"],
        "quality_recip": data["quality_recip"],
        "planes": data["planes"],
        "watch_cells": data["watch_cells"],
        "final_cells": data["final_cells"],
    }


def build_summary() -> dict:
    m4 = load_m4_summary()
    m5 = load_m5_summary()
    sample_x = m4["direct_inverse_sample"]["sample_x"]
    sample_y = m4["direct_inverse_sample"]["sample_y"]
    neighborhood = [
        ("row844_col1603", "witness southwest"),
        ("row844_col1604", "witness southeast"),
        ("row845_col1603", "witness northwest"),
        ("row845_col1604", "witness northeast"),
    ]

    cells = []
    for key, role in neighborhood:
        cell = {"cell": key, "role": role}
        if key in m5["final_cells"]["f250"]:
            cell["f250_rgba"] = m5["final_cells"]["f250"][key]
        elif key in m4["extra_cells"]:
            cell["f250_rgba"] = m4["extra_cells"][key]["f250"]

        if key in m5["final_cells"]["f252"]:
            cell["f252_rgba"] = m5["final_cells"]["f252"][key]

        if key in m5["final_cells"]["e0e"]:
            cell["e0e_rgba"] = m5["final_cells"]["e0e"][key]
        elif key in m4["extra_cells"]:
            bits = m4["extra_cells"][key]["e0e_bits"]
            cell["e0e_rgba_bits"] = bits
        cells.append(cell)

    return {
        "kind": "olmradialblur_case0010_static_witness",
        "case_id": "case_0010",
        "witness_pixel": [1614, 6],
        "source_artifacts": {
            "m4_report": repo_rel(M4_REPORT),
            "m5_json": repo_rel(M5_JSON),
        },
        "buffers": m4["buffers"],
        "render_facts": {
            "angular_cols": m5["angular_cols"],
            "quality_recip": m5["quality_recip"],
            "m5_elapsed_seconds": m5["elapsed_seconds"],
        },
        "final_sampler": {
            "sample_x": sample_x,
            "sample_y": sample_y,
            "direct_inverse_sample": m4["direct_inverse_sample"],
            "output_witness": m4["output_witness"],
        },
        "witness_neighborhood_cells": cells,
        "limitations": [
            "This report reuses existing M4/M5 artifacts and does not perform a fresh emulation run.",
            "The current local artifacts do not include +0xf252 for row844/1604 or row845/1604.",
            "The current local output witness is the mocked output-world byte state plus a direct +0xe sampler probe; it is not a Windows final-writeback capture.",
        ],
    }


def render_markdown(summary: dict) -> str:
    sampler = summary["final_sampler"]["direct_inverse_sample"]
    output = summary["final_sampler"]["output_witness"]

    lines = [
        "# OLMRadialBlur case_0010 static witness summary",
        "",
        "## FACT",
        "",
        "- This report reuses existing local artifacts rather than rerunning `tools/emulation/test_m4_case0010.py` or `tools/emulation/test_m5_case0010_cell_writes.py`.",
        f"- Source artifacts: `{summary['source_artifacts']['m4_report']}` and `{summary['source_artifacts']['m5_json']}`.",
        f"- Buffers from the captured run: `f250={summary['buffers']['f250']}`, `f252={summary['buffers']['f252']}`, `+0xe={summary['buffers']['e0e']}`.",
        f"- Render facts carried forward from M5: `angular_cols={summary['render_facts']['angular_cols']}`, `quality_recip={summary['render_facts']['quality_recip']}`, `elapsed={summary['render_facts']['m5_elapsed_seconds']:.2f}s`.",
        f"- Final-sampler probe for `case_0010 (1614,6)`: radius `{sampler['radius']:.9f}`, angle `{sampler['angle']:.9f}`, sample coords `({sampler['sample_x']:.9f}, {sampler['sample_y']:.9f})`, direct `+0xe` RGBA `{tuple(round(v, 9) for v in sampler['e0e_rgba_float'])}`, u8 `{tuple(sampler['u8'])}`.",
        f"- Local output-world bytes for `(1614,6)`: ARGB `{tuple(output['argb_bytes'])}`, RGBA `{tuple(output['rgba_bytes'])}`.",
        "",
        "## Witness Neighborhood",
        "",
        "| Cell | Role | `+0xf250.rgba` | `+0xf252` | collapsed `+0xe.rgba` |",
        "| --- | --- | --- | --- | --- |",
    ]

    for cell in summary["witness_neighborhood_cells"]:
        f250 = cell.get("f250_rgba", "n/a")
        f252 = cell.get("f252_rgba", "n/a")
        if "e0e_rgba" in cell:
            e0e = cell["e0e_rgba"]
        else:
            e0e = cell.get("e0e_rgba_bits", "n/a")
        lines.append(
            f"| `{cell['cell']}` | {cell['role']} | `{f250}` | `{f252}` | `{e0e}` |"
        )

    lines.extend(
        [
            "",
            "## INFERENCE",
            "",
            "- This bounded summary complements the planned Windows same-run final-writeback/provenance witness; it does not replace it.",
            "- The local artifacts are already enough to restate the black direct-sampler outcome for `(1614,6)` without another multi-minute rerun.",
            "- They are not enough to prove the missing Windows relation for `+0xf252 -> +0xe.alpha -> final output` at both col1603 and col1604, because the current local capture lacks `+0xf252` for the `1604` column and lacks a true Windows final-writeback dump.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    summary = build_summary()
    OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(summary), encoding="utf-8")
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
