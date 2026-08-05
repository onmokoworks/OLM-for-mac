#!/usr/bin/env python3
"""PF16 Zoom offset mode 2/UI 2 actual-AEX/production fixture."""

import json
import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as fixture

fixture.OUTER_STRENGTH = 4
fixture.OUTER_OFFSET_MODE = 2
fixture.OUTER_OFFSET = 2
fixture.KIND = "olmradialblur_zoom_pf16_offset_mode2_ui2_small_actual_aex_20260805"
fixture.SCOPE = (
    "independent PF16 Zoom outer offset mode 2/UI 2, Strength 4, padded 9x7; "
    "structural max(strength, offset) worker boundary, no Rotation fixture reuse or AE-host claim"
)
fixture.fixture.FIXTURE = fixture.fixture.ROOT / "refs/fixtures/olmradialblur_zoom_pf16_offset_mode2_ui2_small_20260805"
fixture.fixture.REPORT = fixture.fixture.ROOT / "refs/conformance/olmradialblur_zoom_pf16_offset_mode2_ui2_small_actual_aex_20260805.json"
fixture.fixture.EXPECTED = {
    "source_pf16": ("d059727f9096038fea75037a9ba49b82f99c9dd84fd74b15fb11b09f72ca6f85", "5a57d8c8f898bfc576ba38654a81eccf47635c5c30314d59c7c86e8a8ab29f55"),
    "pre_blur": ("27c95680ec8f1d897eeddcd456456bfad1ae1406c121e7f39a6a1e9863d72dc0", "25ea86099c1168b122dba225079c1708b3e67695ac7613ca4d72b47cbf03ed5a"),
    "post_blur": ("d85a97a70daaab76fb339bcb21b31125e88b87c076bbe5005b1216e8374140ab", "85503846b2a43c3abc21102cec5108ee9c30b11e4efeeeb96295d4099959a25c"),
    "output": ("0b0bff1ccc6023d1583775165dde69dd2d0b0f97e7af946062f737ab6fc893aa", "7ac84c2629e7a7ae4dc1865583906f829903b0bbf0ad51b2a3cb819f408ab096"),
}


def main():
    code = fixture.main()
    report = json.loads(fixture.fixture.REPORT.read_text())
    report["structural_boundary"] = {
        "outer_offset_mode": 2,
        "outer_offset_ui": 2,
        "worker_offset_zero_based": 1,
        "selection_rule": "max(strength, offset)",
        "classification": "previously unproved Zoom mode-2 worker path",
        "not_a_strength_value_variant": True,
    }
    fixture.fixture.REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
