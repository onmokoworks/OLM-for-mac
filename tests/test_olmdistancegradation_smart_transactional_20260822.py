from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
HARNESS = ROOT / "tools/emulation/dg_public_smart_owner_contract_harness_20260812.cpp"


class DistanceGradationSmartTransactionalTests(unittest.TestCase):
    def test_commit_follows_all_parameter_and_layer_cleanup(self):
        source = SOURCE.read_text()
        start = source.index("SmartRender(PF_InData")
        end = source.index("// ============================================================================\n// Entry point", start)
        body = source[start:end]
        self.assertIn("olm::world_safety::TightStaging staging", body)
        self.assertIn("staging.prepare", body)
        self.assertIn("render_complete = !err", body)
        self.assertIn("staging.commit()", body)
        self.assertLess(body.index("PF_CHECKIN_PARAM"), body.index("staging.commit()"))
        self.assertLess(body.index("checkin_layer_pixels"), body.index("staging.commit()"))

    def test_public_smart_contract_is_atomic_under_sanitizers(self):
        # Reuse the complete public-owner lifecycle probe, strengthening its two
        # historical cleanup cases from "may change" to "must remain unchanged".
        source = HARNESS.read_text()
        source = source.replace(
            '#include "dg_renderbits_real_harness_20260716_sdk_shim.h"',
            '#include "tools/emulation/dg_renderbits_real_harness_20260716_sdk_shim.h"',
        ).replace(
            '#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"',
            '#include "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"',
        ).replace(
            "const bool output_may_change=which==15||which==16;",
            "const bool output_may_change=false;",
        ).replace(
            "result->max_result_rect = {0, 0, W, H};",
            "result->max_result_rect = {0, 0, W, H}; result->ref_width=W; result->ref_height=H;",
        ).replace(
            "PF_InData in{}; in.downsample_x={1,1};",
            "PF_InData in{}; in.width=W; in.height=H; in.downsample_x={1,1};",
        ).replace(
            "if(which==21)dg_harness_fail_color=true;",
            "if(which==21)dg_harness_fail_color=true;"
            "if(which==22)ow.data=(decltype(ow.data))(input.data()+sizeof(PF_PixelFloat));",
        )
        self.assertIn("const bool output_may_change=false;", source)
        source = source[:source.rindex("int main(){")] + (
            "int main(){"
            "if(int e=negative_pf32(15)) return e;"
            "if(int e=negative_pf32(16)) return e;"
            "if(int e=negative_pf32(22)) return e;"
            "return 0;}\n"
        )
        with tempfile.TemporaryDirectory(prefix="olmdg-smart-atomic-") as raw:
            cpp = Path(raw) / "probe.cpp"
            exe = Path(raw) / "probe"
            cpp.write_text(source)
            build = subprocess.run(
                ["clang++", "-std=c++17", "-O1", "-g", "-fno-fast-math",
                 "-ffp-contract=off", "-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer", "-I", str(ROOT), "-I",
                 str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"), str(cpp),
                 str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(exe)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run(
                [str(exe)], cwd=ROOT, text=True, capture_output=True,
                env={**os.environ, "ASAN_OPTIONS": "halt_on_error=1",
                     "UBSAN_OPTIONS": "halt_on_error=1"}, timeout=180,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertNotIn("runtime error:", run.stderr)


if __name__ == "__main__":
    unittest.main()
