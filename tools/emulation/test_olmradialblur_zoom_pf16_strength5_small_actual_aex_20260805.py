#!/usr/bin/env python3
"""PF16 Zoom Outer Strength 5 actual-AEX/production fixture."""

import json
import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as fixture

fixture.OUTER_STRENGTH = 5
fixture.OUTER_OFFSET_MODE = 1
fixture.OUTER_OFFSET = 0
fixture.KIND = "olmradialblur_zoom_pf16_strength5_small_actual_aex_20260805"
fixture.SCOPE = (
    "independent PF16 Zoom outer-only Strength 5, mode 1/offset 0, padded 9x7; "
    "distinct from PF16 Strength 4 and no Rotation fixture reuse or AE-host claim"
)
fixture.fixture.FIXTURE = fixture.fixture.ROOT / "refs/fixtures/olmradialblur_zoom_pf16_strength5_small_20260805"
fixture.fixture.REPORT = fixture.fixture.ROOT / "refs/conformance/olmradialblur_zoom_pf16_strength5_small_actual_aex_20260805.json"
fixture.fixture.EXPECTED = {
    "source_pf16": ("d059727f9096038fea75037a9ba49b82f99c9dd84fd74b15fb11b09f72ca6f85", "5a57d8c8f898bfc576ba38654a81eccf47635c5c30314d59c7c86e8a8ab29f55"),
    "pre_blur": ("27c95680ec8f1d897eeddcd456456bfad1ae1406c121e7f39a6a1e9863d72dc0", "25ea86099c1168b122dba225079c1708b3e67695ac7613ca4d72b47cbf03ed5a"),
    "post_blur": ("0640ff0e062548e8abad32025d60d534063a7a0d338c1a0b17b1881908efbb54", "c477c5c3b446280c4af1d9191d5096f6f16d73b7571d44dd865ed327edf3a6ef"),
    "output": ("84b9f2a4c6f9c48cde49b051ea70d0029f9ef0db458fc522e2923c8da83a9430", "4139e1e6d329102e8e0a7893e3396687c2e87da1eddc1c50f0674b661ac74db6"),
}


def main():
    code = fixture.main()
    report = json.loads(fixture.fixture.REPORT.read_text())
    report["parameter_branch"].update({
        "baseline_outer_strength": 4,
        "effective_length": 5,
        "actual_post_blur_differs_from_strength4": True,
        "actual_output_differs_from_strength4": True,
    })
    report["non_overlap"]["reason"] = (
        "Independent PF16 source execution with Zoom Strength 5; its post-blur plane and PF16 output hashes differ from the Strength 4 fixture."
    )
    fixture.fixture.REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
