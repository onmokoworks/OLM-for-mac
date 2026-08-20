from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
HARNESS = ROOT / "tools/emulation/olmsmoother2_public_guard_harness_20260812.cpp"


class OLMSmoother2RoiContract(unittest.TestCase):
    def test_smart_world_authority_uses_origin_not_content_extent(self) -> None:
        text = PORT.read_text(encoding="utf-8")
        validate = text.split("ValidatePublicWorlds(", 1)[1].split("// Classic Render", 1)[0]
        self.assertNotIn("extent_hint", validate)
        for token in (
            "input->origin_x != 0", "input->origin_y != 0",
            "output->origin_x != 0", "output->origin_y != 0",
        ):
            self.assertIn(token, validate)

    def test_classifier_has_unbounded_frame_edge_walkers(self) -> None:
        text = PORT.read_text(encoding="utf-8")
        # These are opposite-direction cardinal walkers used by the classifier.
        # Their bounds are the image edges, not a constant support radius.
        for token in (
            "scan_d0d0",  # up to y=0
            "scan_d520",  # left to x=0
            "while (y < hMax)",  # down to bottom edge
            "while (x < wMax)",  # right to right edge
        ):
            self.assertIn(token, text)

        # Counterexample for every proposed finite halo H: the center's run
        # length changes when one remote terminating sample moves from H+1 to
        # H+2, although the H-neighborhood is identical.
        for halo in (0, 1, 2, 7, 31):
            near = [1] * (halo + 2) + [0]
            far = [1] * (halo + 3) + [0]
            self.assertEqual(near[: halo + 1], far[: halo + 1])
            self.assertNotEqual(near.index(0), far.index(0))

    def test_prerender_requires_verified_full_frame_checkout(self) -> None:
        compiler = shutil.which("clang++")
        if not compiler:
            self.skipTest("clang++ unavailable")
        program = f'''\
#define main retained_guard_main
#include "{HARNESS}"
#undef main

static bool wrong_ref = false;
static PF_Err checkout(PF_ProgPtr, A_long, A_long, PF_RenderRequest *req,
                       A_long, A_long, A_long, PF_CheckoutResult *r) {{
    if (req->rect.left != 0 || req->rect.top != 0 ||
        req->rect.right != 37 || req->rect.bottom != 23 ||
        !req->preserve_rgb_of_zero_alpha) return 91;
    r->ref_width = wrong_ref ? 36 : 37; r->ref_height = 23;
    // Transparent source: content bounds are legitimately empty even though
    // the checked-out buffer authority is the complete 37x23 frame.
    r->result_rect = r->max_result_rect = PF_LRect{{0, 0, 0, 0}};
    return 0;
}}

int main() {{
    {{
        Fixture f(8, 19, 17, 5);
        std::memset(f.defs, 0, sizeof(f.defs));
        f.defs[SM_INPUT].u.ld = f.iw;
        f.defs[SM_KEY_COLOR].u.cd.value = {{255,255,255,255}};
        f.defs[SM_SMOOTHNESS].u.sd.value = 0;
        f.defs[SM_VERSION].u.pd.value = SMOOTHER_V2;
        f.defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
        f.defs[SM_GAMMA_VALUE].u.fs_d.value = (double)(float)2.4f;
        f.defs[SM_NUM_GAMMA_COLORS].u.sd.value = 1;
        f.iw.extent_hint = f.ow.extent_hint = PF_LRect{{0,0,0,0}};
        if (Smart(f)) return 10; // transparent content bounds are not buffer bounds
        f.ow.origin_x = 1;
        if (!Smart(f)) return 11;
    }}
    for (short depth : {{8, 16, 32}}) {{
        PF_InData in{{}}; PF_OutData out{{}};
        in.width = 37; in.height = 23;
        in.downsample_x = {{1,1}}; in.downsample_y = {{1,1}};
        PF_PreRenderInput pri{{}}; pri.bitdepth = depth;
        pri.output_request.rect = PF_LRect{{11, 7, 19, 13}};
        PF_PreRenderOutput pro{{}};
        PF_PreRenderCallbacks cb{{}}; cb.checkout_layer = checkout;
        PF_PreRenderExtra ex{{&pri, &pro, &cb}};
        if (EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out, nullptr, nullptr, &ex)) return 1;
        if (pro.result_rect.left != 0 || pro.result_rect.top != 0 ||
            pro.result_rect.right != 37 || pro.result_rect.bottom != 23 ||
            !(pro.flags & PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS)) return 2;
        wrong_ref = true;
        PF_PreRenderOutput bad{{}};
        PF_PreRenderExtra bx{{&pri, &bad, &cb}};
        if (!EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out, nullptr, nullptr, &bx)) return 3;
        wrong_ref = false;
    }}
    return 0;
}}
'''
        with tempfile.TemporaryDirectory(prefix="smoother2-roi-") as tmp:
            source = Path(tmp) / "probe.cpp"
            binary = Path(tmp) / "probe"
            source.write_text(program, encoding="utf-8")
            subprocess.run(
                [compiler, "-std=c++17", "-O1", "-g", "-fsanitize=address,undefined",
                 "-I", str(ROOT / "cli/OLMSmoother2/shim"),
                 "-I", str(ROOT / "mac/OLMSmoother2"), str(source), "-o", str(binary)],
                check=True,
            )
            subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    unittest.main()
