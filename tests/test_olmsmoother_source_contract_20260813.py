from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[1] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.emulation.olm_assets import resolve_asset

import hashlib
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmsmoother_source_contract_20260813.cpp"
V1 = ROOT / "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
V2 = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

V1_HASHES = {
    "d0851831db13ec2452b9ac20245f8d308d09dad1cf32984b91d4fb950d5945cd",
    "86bbf709af011be19543e165d3e636283f29d4d7189101718ce9aabb9295a56b",
    "63676c82d06b6b7a5542ec04aa6d9aa903f23eda582121cf287cd2dc9ade006c",
    "460efe22ab70b9f168464df2c5ee2c924e556d09afd8d8ddcdc58328ad71b1ce",
    "9d0ab1b7cdcea3d5edc62aa4adbfae9d9e107639b5514ef265cd91d0e7d06fe0",
    "59c23331927b5c90bbad8bb5e8e0c7742e93e1cc38cf6600e94665b1e3b9cf98",
    "1941a4ca2263d87a0021232df8ffae13babc399e2669128d78602bbf1da8821b",
    "9b17bb75ab3f845aa49b61025160322a75cb592918dda3b5effb367b2ebd6e5b",
    "6487e12e6f63fb72ef6f0726064e9e7bfe9f472c76885c2ae0c4be628c887f83",
    "79a69ffb49caaf0d95b72096a51871c42b3e69203c033466f63c74b10757f001",
    "18df1e2648e8a4f25f633f90143c61c5b58fd7e00bfd3bd02013c65947122749",
}

V2_HASHES = {
    "1c15f67a9d0818a0a0266971720e855acac70a89e2690ccbedf5e142fc1c64f3",
    "c8d5ded0f9da071eb9e14e7bf20300916a3b8b292f081099d25dfc6359bbafa2",
    "133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b",
    "4e43421598bfe27755f2b920014c8d3446413061900c9f94e16102fcf3089630",
    "ca56c65ec9209d52c956f40e51cb8f7c133a001eab1b141b95c04295917cce99",
    "66127e3fbe12b1b39f25127550d006f69db7d8aabe9c571f8caf91fc6819dee7",
    "decb2060f0d96ad30146658c2026edae48caf134311b4207d846317c5589467f",
    "c36c335071f2479526394e667d0448932638fa50b082ae7f82e749b48bc8e964",
    "550b73ca84e8b69fa24b8b61e6ee8580ed743b765a15256174c1448999247418",
    "76c868f51c9ac8da08c67f52e8d837401c5457045a659ee7c484f42f69cb252a",
    "c1f989b1abdcc5e2fe6fe46bfe2fb3e769c2f8288ab09ee5005a9db41c4edd6e",
    "22890ba4876617ed2956c87596198c021c26e9e57a67b3816a6c67cf6c8d671e",
    "57431e5864c4c0feecb55a6e1646ae2d0b55417bcdd70d5c03ce814f3c1b12ad",
    "bcdc96e0773448fb52f12907dd4bb6c39addaac7f1bed8f31182bc8ce37dd595",
    "83bab2bff36972c9dbb3d079739a23a18d64179da6d8202e1024af6488fb2a40",
    "d0a57665d75ac51539e2e27e17eae4d16a3916b964ed556bae1bfc553441ad2f",
}

V1_BY_FIXTURE = {
    "fullframe_pf8": "d0851831db13ec2452b9ac20245f8d308d09dad1cf32984b91d4fb950d5945cd",
    "checker_pf8": "86bbf709af011be19543e165d3e636283f29d4d7189101718ce9aabb9295a56b",
    "checker_pf16": "63676c82d06b6b7a5542ec04aa6d9aa903f23eda582121cf287cd2dc9ade006c",
    "colored_pf8": "460efe22ab70b9f168464df2c5ee2c924e556d09afd8d8ddcdc58328ad71b1ce",
    "colored_pf16": "9d0ab1b7cdcea3d5edc62aa4adbfae9d9e107639b5514ef265cd91d0e7d06fe0",
    "ramp_pf8": "59c23331927b5c90bbad8bb5e8e0c7742e93e1cc38cf6600e94665b1e3b9cf98",
    "ramp_pf16": "1941a4ca2263d87a0021232df8ffae13babc399e2669128d78602bbf1da8821b",
    "practical_7x5_pf16": "9b17bb75ab3f845aa49b61025160322a75cb592918dda3b5effb367b2ebd6e5b",
    "practical_64x36_pf16": "6487e12e6f63fb72ef6f0726064e9e7bfe9f472c76885c2ae0c4be628c887f83",
    "constant_exact_5x3_pf16": "79a69ffb49caaf0d95b72096a51871c42b3e69203c033466f63c74b10757f001",
    "constant_near_5x3_pf16": "18df1e2648e8a4f25f633f90143c61c5b58fd7e00bfd3bd02013c65947122749",
}

V2_BY_FIXTURE = {
    "v2_3x2_pf32": "4e43421598bfe27755f2b920014c8d3446413061900c9f94e16102fcf3089630",
    "v2_5x5_gamma18_pf8": "ca56c65ec9209d52c956f40e51cb8f7c133a001eab1b141b95c04295917cce99",
    "v2_5x5_gamma18_pf16": "66127e3fbe12b1b39f25127550d006f69db7d8aabe9c571f8caf91fc6819dee7",
    "v2_5x5_gamma18_pf32": "decb2060f0d96ad30146658c2026edae48caf134311b4207d846317c5589467f",
    "v2_5x5_gamma24_pf8": "c36c335071f2479526394e667d0448932638fa50b082ae7f82e749b48bc8e964",
    "v2_5x5_gamma24_pf16": "550b73ca84e8b69fa24b8b61e6ee8580ed743b765a15256174c1448999247418",
    "v2_5x5_gamma24_pf32": "76c868f51c9ac8da08c67f52e8d837401c5457045a659ee7c484f42f69cb252a",
    "v2_17x11_pf8_straight": "c1f989b1abdcc5e2fe6fe46bfe2fb3e769c2f8288ab09ee5005a9db41c4edd6e",
    "v2_17x11_pf8_premul": "22890ba4876617ed2956c87596198c021c26e9e57a67b3816a6c67cf6c8d671e",
    "v2_17x11_pf16_straight": "57431e5864c4c0feecb55a6e1646ae2d0b55417bcdd70d5c03ce814f3c1b12ad",
    "v2_17x11_pf16_premul": "bcdc96e0773448fb52f12907dd4bb6c39addaac7f1bed8f31182bc8ce37dd595",
    "v2_17x11_pf32_straight": "d0a57665d75ac51539e2e27e17eae4d16a3916b964ed556bae1bfc553441ad2f",
    "v2_17x11_pf32_premul": "83bab2bff36972c9dbb3d079739a23a18d64179da6d8202e1024af6488fb2a40",
}

V1_SOURCE_ORDER = [V1_BY_FIXTURE[name] for name in (
    "fullframe_pf8","checker_pf8","checker_pf16","colored_pf8","colored_pf16",
    "ramp_pf8","ramp_pf16","practical_7x5_pf16","practical_64x36_pf16",
    "constant_exact_5x3_pf16","constant_near_5x3_pf16")]
V2_SOURCE_ORDER = [V2_BY_FIXTURE[name] for name in (
    "v2_3x2_pf32","v2_5x5_gamma18_pf8","v2_5x5_gamma18_pf16","v2_5x5_gamma18_pf32",
    "v2_5x5_gamma24_pf8","v2_5x5_gamma24_pf16","v2_5x5_gamma24_pf32",
    "v2_17x11_pf8_straight","v2_17x11_pf8_premul","v2_17x11_pf16_straight",
    "v2_17x11_pf16_premul","v2_17x11_pf32_premul","v2_17x11_pf32_straight")]
V2_SOURCE_ORDER.insert(0, "133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b")
V2_SOURCE_ORDER.insert(0, "c8d5ded0f9da071eb9e14e7bf20300916a3b8b292f081099d25dfc6359bbafa2")
V2_SOURCE_ORDER.insert(0, "1c15f67a9d0818a0a0266971720e855acac70a89e2690ccbedf5e142fc1c64f3")

def admission_hash_order(path: Path, function: str, next_function: str) -> list[str]:
    text=re.sub(r'#include "(OLMSmoother[^"\n]+\.inc)"', lambda match: (path.parent / match[1]).read_text(), path.read_text());body=text.split(function,1)[1].split(next_function,1)[0]
    return re.findall(r'"([0-9a-f]{64})"',body)


class SourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(prefix="olmsmoother-source-contract-")
        cls.exe = Path(cls.tmp.name) / "probe"
        subprocess.run([
            _UCRT_CXX, "-std=c++17", "-O2", "-I", str(ROOT),
            str(PROBE), "-o", str(cls.exe),
        ], check=True)
        lines = subprocess.run([str(cls.exe)], check=True, text=True,
                               capture_output=True).stdout.splitlines()
        cls.rows = {parts[1]: parts[2] for line in lines
                    if (parts := line.split()) and parts[0] == "SOURCE"}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_sha256_known_answers(self) -> None:
        self.assertEqual(self.rows["sha256_empty"], hashlib.sha256(b"").hexdigest())
        self.assertEqual(self.rows["sha256_abc"], hashlib.sha256(b"abc").hexdigest())
        payload = bytes((i * 37 + 11) & 255 for i in range(1000))
        self.assertEqual(self.rows["sha256_multiblock"], hashlib.sha256(payload).hexdigest())

    def test_v1_every_fixed_source_is_pinned(self) -> None:
        text = re.sub(r'#include "(OLMSmoother[^"\n]+\.inc)"', lambda match: (V1.parent / match[1]).read_text(), V1.read_text())
        self.assertTrue(all(value in text for value in V1_HASHES))
        self.assertIn("V1SourceIs", text)

    def test_v1_tuple_to_digest_placement_is_exact(self) -> None:
        self.assertEqual(admission_hash_order(V1,"V1ClassicAdmission(","ValidatePublicWorlds("),V1_SOURCE_ORDER)

    def test_v1_probe_matches_every_fixture_digest(self) -> None:
        sys.path.insert(0, str(ROOT / "tools/emulation"))
        import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as checker
        import test_olmsmoother_v1_colored_fractional_alpha_actual_aex_20260811 as colored
        import test_olmsmoother_v1_multivalue_ramp_boundary_20260810 as ramp
        import test_olmsmoother_v1_pf16_practical_geometry_actual_aex_20260812 as practical
        from PIL import Image

        def active_digest(payload: bytes, rowbytes: int, active_bytes: int, height: int) -> str:
            active = b"".join(payload[y * rowbytes:y * rowbytes + active_bytes]
                              for y in range(height))
            return hashlib.sha256(active).hexdigest()

        observed = {}
        for name, fixture in (("checker",checker.fixture),("colored",colored.fixture),("ramp",ramp.fixture)):
            for depth in (8, 16):
                payload, rowbytes = fixture(depth)
                observed[f"{name}_pf{depth}"] = active_digest(payload, rowbytes,
                                                              7 * (4 if depth == 8 else 8), 5)
        for width, height, padding in ((64, 36, 32), (7, 5, 8)):
            payload, rowbytes = practical.fixture(width, height, padding)
            observed[f"practical_{width}x{height}_pf16"] = active_digest(payload, rowbytes, width * 8, height)

        key = tuple(checker.widen(value) for value in checker.KEY)
        for name,pixel in (("constant_exact_5x3_pf16",(0x8000, *key)), ("constant_near_5x3_pf16",(0x8000, key[0] + 1, key[1], key[2]))):
            active = struct.pack("<4H", *pixel) * 5 * 3
            observed[name] = hashlib.sha256(active).hexdigest()

        source = Image.open(resolve_asset(ROOT / "refs/win_references/20260604_olm/OLMSmoother/case_0001_before_effects.png")).convert("RGBA")
        argb = b"".join(bytes((a, r, g, b)) for r, g, b, a in source.getdata())
        observed["fullframe_pf8"] = hashlib.sha256(argb).hexdigest()
        self.assertEqual(observed, V1_BY_FIXTURE)

    def test_v2_probe_matches_every_fixture_digest(self) -> None:
        probe_hashes = {key:value for key,value in self.rows.items() if key.startswith("v2_")}
        self.assertEqual(probe_hashes, V2_BY_FIXTURE)

    def test_v2_every_fixed_source_is_pinned(self) -> None:
        text = re.sub(r'#include "(OLMSmoother[^"\n]+\.inc)"', lambda match: (V2.parent / match[1]).read_text(), V2.read_text())
        self.assertTrue(all(value in text for value in V2_HASHES))
        self.assertIn("V2SourceIs", text)

    def test_v2_tuple_to_digest_placement_is_exact(self) -> None:
        self.assertEqual(admission_hash_order(V2,"V2SmartAdmission(","ValidatePublicWorlds("),V2_SOURCE_ORDER)

    def test_wrong_pf16_17x11_hashes_are_absent(self) -> None:
        text = re.sub(r'#include "(OLMSmoother[^"\n]+\.inc)"', lambda match: (V2.parent / match[1]).read_text(), V2.read_text())
        self.assertNotIn("d149fda08b3cf73939e38a47532a35dce872aa86699fd5eb0b57158140f3e970", text)
        self.assertNotIn("c763aa96ccce97f4d1b6df85d2357ef6cdc36ac2b0a3b592aa5c1c7feca3e444", text)


if __name__ == "__main__":
    unittest.main()
