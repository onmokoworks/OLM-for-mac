from __future__ import annotations

import importlib.util
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_aexcompat_reference.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_aexcompat_reference_20260725", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunAexcompatReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="run_aexcompat_reference_20260725_"))
        self.module = load_module()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def _write_png(self, path: Path, *, size: tuple[int, int], color: tuple[int, int, int, int]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", size, color).save(path)

    def _request_root(self) -> Path:
        root = self.tmp / "request"
        (root / "input").mkdir(parents=True, exist_ok=True)
        (root / "expected").mkdir(parents=True, exist_ok=True)
        return root

    def _write_reference_manifest(self, root: Path, cases: list[dict]) -> Path:
        manifest = {"project": {"bits_per_channel": 8}, "cases": cases}
        path = root / "reference_manifest.json"
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return path

    def _zip_tree(self, source: Path, target: Path) -> Path:
        with zipfile.ZipFile(target, "w") as archive:
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(source))
        return target

    def _write_fake_worker(self, path: Path) -> Path:
        source = """#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from PIL import Image


def parse_params(values):
    result = {}
    for value in values:
        name, raw = value.split("=", 1)
        result[name.split("@", 1)[0]] = raw
    return result


def main():
    mode = sys.argv[1]
    if mode == "setup":
        print(
            json.dumps(
                {
                    "parameters": [
                        {"name": "Blur Amount", "slot": 1, "param_type": 1},
                        {"name": "Legacy", "slot": 2, "param_type": 4},
                    ]
                }
            )
        )
        return 0
    if mode not in {"render-png", "render-trace-png"}:
        print(f"unsupported mode: {mode}", file=sys.stderr)
        return 9
    input_path = Path(sys.argv[3])
    output_path = Path(sys.argv[4])
    params = parse_params(sys.argv[5:])
    with Image.open(input_path) as image:
        rgba = image.convert("RGBA")
        if params.get("Blur Amount") == "2":
            original = rgba.getpixel((0, 0))
            rgba.putpixel((0, 0), (original[0] ^ 1, original[1], original[2], original[3]))
        rgba.save(output_path)
    print(
        json.dumps(
            {
                "render_error": 7 if params.get("Blur Amount") == "3" else 0,
                "render_mode": mode,
                "execution_traces": [],
                "received_params": sys.argv[5:],
            }
        )
    )
    return 0


raise SystemExit(main())
"""
        path.write_text(source, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def test_case_parameters_filters_manifest_to_worker_surface(self) -> None:
        case = {
            "id": "case_0001",
            "effects": [
                {
                    "params": [
                        {"name": "Blur Amount", "value": 129.4},
                        {"name": "Ignored Param", "value": 777},
                        {"name": "Legacy", "value": False},
                    ]
                }
            ],
        }

        actual = self.module.case_parameters(case, {"Blur Amount", "Legacy"})

        self.assertEqual(
            actual,
            [("Blur Amount", None, 129.4), ("Legacy", None, 0.0)],
        )

    def test_case_parameters_accepts_two_dimensional_point(self) -> None:
        case = {
            "id": "case_point",
            "effects": [
                {
                    "params": [
                        {"name": "Center", "value": [12.5, -7.25]},
                    ]
                }
            ],
        }

        actual = self.module.case_parameters(case, {"Center"})

        self.assertEqual(actual, [("Center", None, (12.5, -7.25))])
        self.assertEqual(
            self.module.format_parameter_assignment(*actual[0]),
            "Center=12.5,-7.25",
        )

    def test_case_parameters_uses_slots_for_duplicate_names(self) -> None:
        case = {
            "id": "case_slots",
            "effects": [
                {
                    "params": [
                        {
                            "path": ["OLM RadialBlur", "Center"],
                            "name": "Center",
                            "property_index": 2,
                            "value": [720, 805],
                        },
                        {
                            "path": ["OLM RadialBlur", "Strength"],
                            "name": "Strength",
                            "property_index": 4,
                            "value": 917,
                        },
                        {
                            "path": ["OLM RadialBlur", "Strength"],
                            "name": "Strength",
                            "property_index": 10,
                            "value": 1222,
                        },
                        {
                            "path": [
                                "OLM RadialBlur",
                                "Compositing Options",
                                "GPU Rendering",
                            ],
                            "name": "GPU Rendering",
                            "property_index": 2,
                            "value": 1,
                        },
                    ]
                }
            ],
        }
        surface = [
            {"slot": 2, "name": "Center", "param_type": 6},
            {"slot": 4, "name": "Strength", "param_type": 1},
            {"slot": 10, "name": "Strength", "param_type": 1},
        ]

        actual = self.module.case_parameters(case, surface)

        self.assertEqual(
            actual,
            [
                ("Center", 2, (720.0, 805.0)),
                ("Strength", 4, 917.0),
                ("Strength", 10, 1222.0),
            ],
        )
        self.assertEqual(
            [self.module.format_parameter_assignment(*row) for row in actual],
            ["Center@2=720,805", "Strength@4=917", "Strength@10=1222"],
        )

    def test_case_parameters_converts_rgba_float_to_slot_qualified_argb8(self) -> None:
        case = {
            "id": "case_color",
            "effects": [
                {
                    "params": [
                        {
                            "path": ["OLM Smoother2", "Color Key"],
                            "name": "Color Key",
                            "property_index": 2,
                            "value": [1, 0, 0.47058817744255, 1],
                        }
                    ]
                }
            ],
        }
        surface = [{"slot": 2, "name": "Color Key", "param_type": 5}]

        values = self.module.case_parameters(case, surface)
        self.assertEqual(values, [("Color Key", 2, (255, 255, 0, 120))])
        self.assertEqual(
            self.module.format_parameter_assignment(*values[0]),
            "Color Key@2=255,255,0,120",
        )

    def test_color_conversion_rejects_non_normalized_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside 0..1"):
            self.module.rgba_float_to_argb8([1, 0, 1.01, 1])

    def test_missing_parameter_error_keeps_slot_name_and_type(self) -> None:
        case = {
            "id": "case_missing",
            "effects": [
                {
                    "params": [
                        {
                            "path": ["OLM Blur", "Repeat"],
                            "name": "Repeat",
                            "property_index": 2,
                            "value": 1,
                        }
                    ]
                }
            ],
        }
        surface = [
            {"slot": 1, "name": "Blur Amount", "param_type": 1},
            {"slot": 2, "name": "Repeat", "param_type": 4},
        ]

        with self.assertRaisesRegex(
            ValueError,
            r"case_missing: manifest is missing AEX parameters: \['1:Blur Amount:slider'\]",
        ):
            self.module.case_parameters(case, surface)

    def test_parameter_format_round_trips_without_six_digit_rounding(self) -> None:
        value = 0.12345678901234566

        encoded = self.module.format_parameter_value(value)

        self.assertEqual(float(encoded), value)
        self.assertNotEqual(encoded, f"{value:g}")

    def test_manifest_rejects_explicit_non_8bpc(self) -> None:
        self.module.require_argb8_manifest({"project": {"bits_per_channel": 8}})
        self.module.require_argb8_manifest({"project": {}})

        with self.assertRaisesRegex(ValueError, "only 8bpc"):
            self.module.require_argb8_manifest({"project": {"bits_per_channel": 16}})

    def test_resolve_case_image_accepts_nested_and_legacy_flat_layouts(self) -> None:
        root = self.tmp / "request"
        nested = root / "input" / "nested.png"
        flat = root / "flat.png"
        self._write_png(nested, size=(1, 1), color=(0, 0, 0, 255))
        self._write_png(flat, size=(1, 1), color=(0, 0, 0, 255))

        self.assertEqual(
            self.module.resolve_case_image(root, "input", "nested.png"),
            nested,
        )
        self.assertEqual(
            self.module.resolve_case_image(root, "input", "flat.png"),
            flat,
        )

    def test_run_case_rejects_16bit_png_before_worker_execution(self) -> None:
        root = self._request_root()
        for directory in ("input", "expected"):
            Image.new("I;16", (4, 4), 1024).save(root / directory / "probe.png")
        case = {
            "id": "case_16bit",
            "before_effects_frame": "probe.png",
            "frame": "probe.png",
            "effects": [{"params": []}],
        }

        with self.assertRaisesRegex(ValueError, "requires an 8-bit PNG"):
            self.module.run_case(
                worker=self.tmp / "missing-worker",
                aex=self.tmp / "missing.aex",
                manifest_root=root,
                case=case,
                accepted_parameters=set(),
                output_dir=self.tmp / "out",
                trace=False,
                allow_large_trace=False,
                timeout=1,
            )

    def test_pixel_diff_reports_exact_and_nonzero_delta(self) -> None:
        exact_a = self.tmp / "exact_a.png"
        exact_b = self.tmp / "exact_b.png"
        diff_a = self.tmp / "diff_a.png"
        diff_b = self.tmp / "diff_b.png"
        self._write_png(exact_a, size=(2, 1), color=(10, 20, 30, 255))
        self._write_png(exact_b, size=(2, 1), color=(10, 20, 30, 255))
        self._write_png(diff_a, size=(2, 1), color=(0, 0, 0, 255))
        self._write_png(diff_b, size=(2, 1), color=(0, 0, 0, 255))
        with Image.open(diff_b) as image:
            rgba = image.convert("RGBA")
            rgba.putpixel((1, 0), (1, 0, 0, 255))
            rgba.save(diff_b)

        exact = self.module.pixel_diff(exact_a, exact_b)
        diff = self.module.pixel_diff(diff_a, diff_b)

        self.assertTrue(exact["exact"])
        self.assertEqual(exact["max_diff"], 0)
        self.assertFalse(diff["exact"])
        self.assertEqual(diff["max_diff"], 1)
        self.assertEqual(diff["nonzero_pixels"], 1)
        self.assertEqual(diff["per_channel_max"], [1, 0, 0, 0])

    def test_run_case_rejects_large_trace_without_override(self) -> None:
        root = self._request_root()
        self._write_png(root / "input" / "large.png", size=(129, 128), color=(1, 2, 3, 255))
        self._write_png(root / "expected" / "large.png", size=(129, 128), color=(1, 2, 3, 255))
        case = {
            "id": "case_large",
            "before_effects_frame": "large.png",
            "frame": "large.png",
            "effects": [{"params": []}],
        }

        with self.assertRaisesRegex(ValueError, "refusing 129x128 trace"):
            self.module.run_case(
                worker=self.tmp / "missing-worker",
                aex=self.tmp / "missing.aex",
                manifest_root=root,
                case=case,
                accepted_parameters=set(),
                output_dir=self.tmp / "out",
                trace=True,
                allow_large_trace=False,
                timeout=1,
            )

    def test_run_case_rejects_nonzero_render_error_even_when_pixels_match(self) -> None:
        root = self._request_root()
        self._write_png(root / "input" / "probe.png", size=(4, 4), color=(1, 2, 3, 255))
        shutil.copyfile(root / "input" / "probe.png", root / "expected" / "probe.png")
        worker = self._write_fake_worker(self.tmp / "fake-worker.py")
        fake_aex = self.tmp / "OLMBlur.aex"
        fake_aex.write_bytes(b"fake-aex\n")
        output_dir = self.tmp / "out"
        output_dir.mkdir()
        case = {
            "id": "case_render_error",
            "before_effects_frame": "probe.png",
            "frame": "probe.png",
            "effects": [
                {
                    "params": [
                        {"name": "Blur Amount", "value": 3},
                        {"name": "Legacy", "value": False},
                    ]
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, "render_error=7"):
            self.module.run_case(
                worker=worker,
                aex=fake_aex,
                manifest_root=root,
                case=case,
                accepted_parameters={"Blur Amount", "Legacy"},
                output_dir=output_dir,
                trace=False,
                allow_large_trace=False,
                timeout=30,
            )

    def test_cli_end_to_end_with_zip_request_filters_params_and_reports_diff(self) -> None:
        request_root = self._request_root()
        shared_input = request_root / "input" / "probe.png"
        self._write_png(shared_input, size=(4, 4), color=(32, 64, 96, 255))
        shutil.copyfile(shared_input, request_root / "expected" / "case_exact.png")
        shutil.copyfile(shared_input, request_root / "expected" / "case_diff.png")
        self._write_reference_manifest(
            request_root,
            [
                {
                    "id": "case_exact",
                    "before_effects_frame": "probe.png",
                    "frame": "case_exact.png",
                    "effects": [
                        {
                            "params": [
                                {
                                    "name": "Blur Amount",
                                    "property_index": 1,
                                    "value": 1,
                                },
                                {
                                    "name": "Legacy",
                                    "property_index": 2,
                                    "value": False,
                                },
                                {"name": "Ignored Param", "value": 999},
                            ]
                        }
                    ],
                },
                {
                    "id": "case_diff",
                    "before_effects_frame": "probe.png",
                    "frame": "case_diff.png",
                    "effects": [
                        {
                            "params": [
                                {
                                    "name": "Blur Amount",
                                    "property_index": 1,
                                    "value": 2,
                                },
                                {
                                    "name": "Legacy",
                                    "property_index": 2,
                                    "value": True,
                                },
                                {"name": "Ignored Param", "value": 999},
                            ]
                        }
                    ],
                },
            ],
        )
        request_zip = self._zip_tree(request_root, self.tmp / "request.zip")
        fake_aex = self.tmp / "OLMBlur.aex"
        fake_aex.write_bytes(b"fake-aex\n")
        worker = self._write_fake_worker(self.tmp / "fake-worker.py")
        output_dir = self.tmp / "output"

        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--request",
                str(request_zip),
                "--aex",
                str(fake_aex),
                "--worker",
                str(worker),
                "--output-dir",
                str(output_dir),
                "--timeout",
                "30",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(proc.returncode, 2, msg=proc.stderr)
        self.assertIn("[EXACT] case_exact max=0 pixels=0", proc.stdout)
        self.assertIn("[DIFF] case_diff max=1 pixels=1", proc.stdout)
        self.assertIn("[SUMMARY] exact=1/2 render_success=2/2 truncated=0", proc.stdout)
        summary = json.loads((output_dir / "AEXCOMPAT_REFERENCE_RESULT.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["counts"]["total"], 2)
        self.assertEqual(summary["counts"]["pixel_exact"], 1)
        self.assertEqual(summary["request_name"], "request.zip")
        self.assertEqual(summary["cases"][0]["comparison"]["exact"], True)
        self.assertEqual(summary["cases"][1]["comparison"]["max_diff"], 1)
        exact_report = json.loads((output_dir / summary["cases"][0]["artifacts"]["worker_report"]).read_text(encoding="utf-8"))
        diff_report = json.loads((output_dir / summary["cases"][1]["artifacts"]["worker_report"]).read_text(encoding="utf-8"))
        self.assertEqual(
            exact_report["received_params"],
            ["Blur Amount@1=1", "Legacy@2=0"],
        )
        self.assertEqual(
            diff_report["received_params"],
            ["Blur Amount@1=2", "Legacy@2=1"],
        )


if __name__ == "__main__":
    unittest.main()
