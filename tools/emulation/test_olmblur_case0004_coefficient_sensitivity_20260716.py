#!/usr/bin/env python3
"""Direct test/report writer for case_0004 coefficient sensitivity A/B."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmblur_case0004_coefficient_sensitivity import run_probe  # noqa: E402

REPORT_JSON = ROOT / "refs/conformance/olmblur_case0004_coefficient_sensitivity_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_case0004_coefficient_sensitivity_20260716.md"


def main() -> int:
    report = run_probe()
    if report["status"] != "pass_bounded_ab":
        raise AssertionError(f"unexpected status: {report['status']}")
    if report["radius_sequence"] != [125, 36, 10, 2]:
        raise AssertionError(f"captured radius sequence differs: {report['radius_sequence']!r}")
    discriminators = report["coefficient_discriminators"]
    if not discriminators or any(abs(item["unsigned_word_delta"]) != 1 for item in discriminators):
        raise AssertionError(f"a coefficient discriminator is not one ULP: {discriminators!r}")
    if len(report["a"]["stages"]) != 16 or len(report["b"]["stages"]) != 16:
        raise AssertionError("portable A/B cone stage coverage differs")
    if any(stage["execution"] != "portable_only" for key in ("a", "b") for stage in report[key]["stages"]):
        raise AssertionError("A/B cone contains non-portable execution")
    supplemental = report["supplemental_index57_only"]
    if len(supplemental["cone"]["stages"]) != 16 or any(
        stage["execution"] != "portable_only" for stage in supplemental["cone"]["stages"]
    ):
        raise AssertionError("index57-only cone contains non-portable or incomplete execution")
    if set(report["standard_writer_prediction"]["comparisons"]) != {"(411,258)", "(458,314)"}:
        raise AssertionError("A/B witness set differs")

    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    conclusion = report["conclusion"]
    lines = [
        "# OLMBlur case_0004 coefficient sensitivity A/B", "", "## FACT", "",
        f"- Captured radius sequence: `{report['radius_sequence']}`.",
        f"- Complete-set coefficient discriminators: `{discriminators}`.",
        f"- Set A: {report['set_labels']['a']}.",
        f"- Set B: {report['set_labels']['b']}.",
        f"- Both use identical staged RGB/flags, radii, pass order, crop geometry, and portable helper implementation across `16` stages.",
        "", "## Witnesses", "",
    ]
    for point, values in report["standard_writer_prediction"]["comparisons"].items():
        lines.append(
            f"- `{point}`: pre-store A `{values['a_pre_store_bits_hex']}`, B `{values['b_pre_store_bits_hex']}`, exact `{values['pre_store_exact']}`; "
            f"predicted RGB words A `{values['a_predicted_rgb_words']}`, B `{values['b_predicted_rgb_words']}`, exact `{values['predicted_words_exact']}`."
        )
    lines.extend([
        "", "## Conclusion", "",
        f"- The complete coefficient-set change alters either final pre-store result: `{conclusion['complete_coefficient_set_changes_pre_store']}`.",
        f"- The complete coefficient-set change alters either standard-writer predicted word: `{conclusion['complete_coefficient_set_changes_predicted_word']}`.",
        f"- Supplemental index-57-only isolation changes either pre-store result: `{conclusion['index57_only_changes_pre_store']}`.",
        f"- Supplemental index-57-only isolation changes either predicted word: `{conclusion['index57_only_changes_predicted_word']}`.",
        "- The index-57 isolation is portable synthetic sensitivity evidence only; authentic set B also differs at iteration 1/index 70.",
        "- Writer values are arithmetic predictions only, not actual-AEX writer observations.",
        "- Neither coefficient set is Windows truth; no Windows, NAS, or SSH execution was used.",
        "", "## Test", "", "```text",
        "python3 tools/emulation/test_olmblur_case0004_coefficient_sensitivity_20260716.py",
        "```", "", "## Changed files", "",
        "- `tools/emulation/probe_olmblur_case0004_coefficient_sensitivity.py` (new)",
        "- `tools/emulation/test_olmblur_case0004_coefficient_sensitivity_20260716.py` (new)",
        "- `refs/conformance/olmblur_case0004_coefficient_sensitivity_20260716.json` (new)",
        "- `refs/conformance/olmblur_case0004_coefficient_sensitivity_20260716.md` (new)",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": report["status"], "conclusion": conclusion,
                      "comparisons": report["standard_writer_prediction"]["comparisons"],
                      "report_json": str(REPORT_JSON.relative_to(ROOT)),
                      "report_md": str(REPORT_MD.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
