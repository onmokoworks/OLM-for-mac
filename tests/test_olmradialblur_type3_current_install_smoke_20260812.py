from __future__ import annotations

import copy
import gzip
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "refs/conformance/olmradialblur_type3_current_install_smoke_20260812.json"
RAW_DIR = ROOT / "refs/conformance/olmradialblur_type3_current_install_smoke_raw_20260812"
OBSERVATION = RAW_DIR / "observation.json"; READY = RAW_DIR / "ready.json"
PNG = RAW_DIR / "default_plumbing.png"; VMMAP_GZ = RAW_DIR / "vmmap.txt.gz"
RUNNER = ROOT / "scripts/run_olmradialblur_type3_current_install_smoke_20260812.py"
POST_CAPTURE_VARIANT = ROOT / "refs/conformance/olmradialblur_type3_current_install_smoke_runner_capture_20260812.py"
PAYLOAD = ROOT / "tools/emulation/olmradialblur_type3_current_install_smoke_payload_20260812.jsx"
SCHEMA = ROOT / "refs/conformance/olmradialblur_type3_current_install_smoke_schema_20260812.json"
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
BUILD = ROOT / "handoff/mac_plugin_builds/olmradialblur_type3_20260812/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
BUILD_IDENTITY = ROOT / "handoff/mac_plugin_builds/olmradialblur_type3_20260812/BUILD_IDENTITY.txt"
BACKUP = ROOT / "handoff/mac_plugin_backups/mediacore_20260812_radial_type3_before_install/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
CLOSURE = ROOT / "refs/conformance/olmradialblur_type3_layer_span_natural_closure_20260812.json"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
SOURCE_SHA = "36063ae68027d97169679b4b234f83ec871cdfed4f936ce6464c7a49cbc71743"
BUILD_SHA = "7701c3cb864ec9a05c82de68d1ab3a57a18f9a9b4f97e3b8d7b1786a016818b3"
BACKUP_SHA = "8a4bd278c3cbffcb924712c6ad20d8c0d70452c4fa2dd4d38fd7373020cd7934"
OBS_SHA = "89ab32443afcc8c1542858cdc3502e484b7012b80e2454e029247282533b1ff6"
READY_SHA = "983933d0b69d693643aeb6216729a732baab1e076bc1c69593ed08fe5e167f8a"
PNG_SHA = "ff6ab6d686cc00e17a2b234d237041fb48c49b8e4ab93609ab0f31cde623bbe3"
GZ_SHA = "6ee6cf98ede2e5c5389d607dd111b57362eb0f93507e9ef5aa564dc0a06e8899"
VMMAP_SHA = "738b290fe77785c22d152e907f30c6e965bac24608cf21c93d42a3fc1a9abe0e"
RUNNER_SHA = "29cc18e4e8d4328793383b4652f1169248b47eb595a5a26336f73d743a36a2c8"
POST_CAPTURE_VARIANT_SHA = "6f27778665de4a740040861869263a27e5e4663711dca2d03b1152f610099932"
PAYLOAD_SHA = "cc05a61edc02dca67b6c6d939453864f83b283da6172f00829c4651047a26dba"
SCHEMA_SHA = "1690e8cfad143b03f0ecf61ae26c26619c12a6c917492df6213eb1a8f4fcd8f8"
CLOSURE_SHA = "72f966198d2cbb8cdfe19ba7dd79ca17f2eb35f41d7c157408fd37dfdfd6b580"
BUILD_IDENTITY_SHA = "dba817141b71492b25022275facc2258357a5f11d079623b0fce963dfb2a2dc8"
SUMMARY_CANONICAL_SHA = "f97c5a1809f1eb832785af5a155da7010eb65234775b33dabf4ecc264c1213c6"
OBSERVATION_CANONICAL_SHA = "2dccbf4868b39ac150b4bcfe8584754eb82c6ef181954689de3a608ce8147393"
INSTALLED_PATH = str(INSTALLED)

def digest_path(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def digest_bytes(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
def canonical_digest(value: dict) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
def load_runner():
    spec = importlib.util.spec_from_file_location("radial_smoke", RUNNER); assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

RUNNER_MODULE = load_runner()

def validates(summary: dict, observation: dict, ready: dict, vmmap: str) -> bool:
    try:
        producer = summary["producer"]; host = summary["host_smoke"]; raw = host["raw_observation"]
        return all([
            canonical_digest(summary) == SUMMARY_CANONICAL_SHA,
            canonical_digest(observation) == OBSERVATION_CANONICAL_SHA,
            summary["schema"] == "olmradialblur-type3-current-install-smoke/1",
            summary["status"] == "installed_host_smoke_pass",
            summary["source"] == {"path": "mac/OLMRadialBlur/OLMRadialBlur.cpp", "sha256": SOURCE_SHA},
            digest_path(SOURCE) == SOURCE_SHA,
            summary["build"]["isolated_bundle"] == "handoff/mac_plugin_builds/olmradialblur_type3_20260812/OLMRadialBlur.plugin",
            summary["build"]["binary_sha256"] == BUILD_SHA, summary["build"]["architectures"] == ["x86_64", "arm64"],
            summary["build"]["identity_transcript"] == "handoff/mac_plugin_builds/olmradialblur_type3_20260812/BUILD_IDENTITY.txt",
            summary["build"]["identity_transcript_sha256"] == BUILD_IDENTITY_SHA == digest_path(BUILD_IDENTITY),
            summary["build"]["codesign"] == "adhoc", summary["build"]["codesign_deep_strict"] is True,
            digest_path(BUILD) == BUILD_SHA, digest_path(BACKUP) == BACKUP_SHA, digest_path(INSTALLED) == BUILD_SHA,
            summary["installed"]["binary_sha256"] == BUILD_SHA, summary["installed"]["matching_bundle_count"] == 1,
            summary["installed"]["bundle"] == "~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin",
            summary["installed"]["previous_binary_sha256"] == BACKUP_SHA,
            summary["installed"]["recoverable_backup"] == "handoff/mac_plugin_backups/mediacore_20260812_radial_type3_before_install/OLMRadialBlur.plugin",
            host["fresh_process"] is True, host["ae_version"] == "26.3x87", host["ae_pid"] == 10809,
            host["application"] == "Adobe After Effects 2026",
            host["renderer"] == "SOFTWARE", host["renderer_raw"] == 1816, host["depth"] == "PF32",
            host["effect_match_name"] == "OLM RadialBlur", host["effect_added"] is True,
            host["module_mapping_persisted"] is True, host["loaded_module_exact_path_segment_count"] == 4,
            host["default_render"] is True, host["default_output_sha256"] == PNG_SHA,
            host["type3"] == "live_type3_timeout", host["type3_parameter_readback_retained"] is False,
            host["pixel_exact"] is False, host["ae_stopped"] is True,
            raw == {"path": "refs/conformance/olmradialblur_type3_current_install_smoke_raw_20260812/observation.json", "sha256": OBS_SHA},
            observation["status"] == "default_render_plumbing_pass_type3_timeout",
            observation["kind"] == "olmradialblur_type3_current_install_smoke_raw_observation_20260812",
            observation["ae"] == {"application": "Adobe After Effects 2026", "version": "26.3x87", "pid": 10809,
                "fresh_process": True, "bits": 32, "renderer_raw": 1816, "renderer": "SOFTWARE",
                "stopped_after_capture": True, "termination": "SIGKILL after Type3 Layer render remained blocked"},
            observation["installed"] == {"binary_path": INSTALLED_PATH, "binary_sha256": BUILD_SHA,
                "matching_bundle_count": 1, "architectures": ["x86_64", "arm64"], "codesign_deep_strict": True},
            observation["ready"]["sha256"] == READY_SHA, observation["module_mapping"]["compressed_sha256"] == GZ_SHA,
            observation["module_mapping"]["uncompressed_sha256"] == VMMAP_SHA,
            observation["module_mapping"]["exact_path_segment_count"] == vmmap.count(INSTALLED_PATH) == 4,
            observation["default_render"]["sha256"] == PNG_SHA, observation["default_render"]["pixel_exact"] is False,
            observation["default_render"] == {"member": "default_plumbing.png", "sha256": PNG_SHA,
                "dimensions": [16, 16], "format": "PNG 16-bit RGBA", "effect_enabled": True, "pixel_exact": False},
            observation["type3_layer"]["attempted"] is True,
            observation["type3_layer"]["noise_layer_match_name"] == "OLM RadialBlur-0021",
            observation["type3_layer"]["parameters_requested"] == RUNNER_MODULE.PARAMETERS,
            observation["type3_layer"]["parameter_readback_retained"] is False,
            observation["type3_layer"]["status"] == "live_type3_timeout",
            observation["type3_layer"]["result_json_created"] is False,
            observation["type3_layer"]["output_created"] is False,
            observation["type3_layer"]["pixel_exact"] is False, observation["type3_layer"]["smart_numerical_exact"] is False,
            ready == {"status": "ready", "ae_version": "26.3x87", "bits": 32, "renderer_raw": 1816, "effect_match_name": "OLM RadialBlur"},
            producer["runner_sha256"] == RUNNER_SHA == digest_path(RUNNER),
            producer["post_capture_variant_sha256"] == POST_CAPTURE_VARIANT_SHA == digest_path(POST_CAPTURE_VARIANT),
            producer["post_capture_variant_relation"] == "Later reconstructed/hardened variant; it did not generate the retained run.",
            "Exact producing runner bytes were not retained" in producer["retained_capture_protocol"],
            producer["payload_sha256"] == PAYLOAD_SHA == digest_path(PAYLOAD),
            producer["schema_sha256"] == SCHEMA_SHA == digest_path(SCHEMA),
            producer["cleanup"] == "runner finally terminates osascript and AE; retained run required SIGKILL after timeout",
            digest_path(OBSERVATION) == OBS_SHA, digest_path(READY) == READY_SHA,
            digest_path(PNG) == PNG_SHA, digest_path(VMMAP_GZ) == GZ_SHA,
            digest_bytes(vmmap.encode()) == VMMAP_SHA, digest_path(CLOSURE) == CLOSURE_SHA,
            summary["separate_hostless_closure"]["sha256"] == CLOSURE_SHA,
            summary["separate_hostless_closure"]["relation"] == "Direct internal-owner and public classic hostless exact evidence remains separate from this AE smoke.",
            summary["claims_not_made"] == [
                "No live AE Type3 Layer pixel-exact or Smart numerical claim",
                "No numerical inference from the default-render PNG",
                "No claim that the timed-out Type3 Layer render completed",
                "No promotion beyond the separately bounded hostless closure"],
        ])
    except (KeyError, TypeError, FileNotFoundError): return False

class RadialType3CurrentInstallSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(SUMMARY.read_text()); cls.observation = json.loads(OBSERVATION.read_text())
        cls.ready = json.loads(READY.read_text()); cls.vmmap = gzip.decompress(VMMAP_GZ.read_bytes()).decode()

    def test_checked_in_evidence_validates(self): self.assertTrue(validates(self.summary, self.observation, self.ready, self.vmmap))

    def test_runner_requires_go_has_cleanup_and_never_installs(self):
        text = RUNNER.read_text()
        self.assertNotIn("ditto", text); self.assertNotIn("copytree", text)
        self.assertIn("explicit GO token required", text); self.assertIn("finally:", text)
        self.assertIn("apple_process.kill()", text); self.assertIn("process.terminate()", text); self.assertIn("process.kill()", text)
        with tempfile.TemporaryDirectory() as directory:
            run = subprocess.run([sys.executable, str(RUNNER), "--execute", "--output", str(Path(directory) / "out")], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2); self.assertIn("explicit GO token required", run.stderr)

    def test_summary_raw_identity_scope_parameter_and_hash_tampering_fails(self):
        mutations = (
            lambda s,o,r,v: s["source"].update(sha256="0"*64),
            lambda s,o,r,v: s["build"].update(binary_sha256="0"*64),
            lambda s,o,r,v: s["installed"].update(matching_bundle_count=2),
            lambda s,o,r,v: s["host_smoke"].update(module_mapping_persisted=False),
            lambda s,o,r,v: s["host_smoke"].update(pixel_exact=True),
            lambda s,o,r,v: s["host_smoke"].update(type3="live_render_plumbing_pass"),
            lambda s,o,r,v: s["host_smoke"]["raw_observation"].update(sha256="0"*64),
            lambda s,o,r,v: o["module_mapping"].update(exact_path_segment_count=3),
            lambda s,o,r,v: o.update(kind="pixel_exact"),
            lambda s,o,r,v: o["ae"].update(termination="normal"),
            lambda s,o,r,v: o["default_render"].update(pixel_exact=True),
            lambda s,o,r,v: o["default_render"].update(format="EXR"),
            lambda s,o,r,v: o["type3_layer"].update(attempted=False),
            lambda s,o,r,v: o["type3_layer"].update(result_json_created=True),
            lambda s,o,r,v: o["type3_layer"].update(output_created=True),
            lambda s,o,r,v: o["type3_layer"].update(noise_layer_match_name="wrong"),
            lambda s,o,r,v: o["type3_layer"]["parameters_requested"].update({"OLM RadialBlur-0019": 24}),
            lambda s,o,r,v: o["type3_layer"].update(parameter_readback_retained=True),
            lambda s,o,r,v: r.update(renderer_raw=0),
            lambda s,o,r,v: s["producer"].update(runner_sha256="0"*64),
            lambda s,o,r,v: s["producer"].update(cleanup="none"),
            lambda s,o,r,v: s["separate_hostless_closure"].update(relation="live proves exact"),
            lambda s,o,r,v: s["claims_not_made"].pop(0),
        )
        for index, mutate in enumerate(mutations):
            s=copy.deepcopy(self.summary); o=copy.deepcopy(self.observation); r=copy.deepcopy(self.ready); v=self.vmmap
            mutate(s,o,r,v)
            with self.subTest(index=index): self.assertFalse(validates(s,o,r,v))

    def test_result_validator_rejects_pixel_promotion(self):
        base = {"status": "ok", "ae_version": "26.3x87", "bits": 32, "renderer_raw": 1816,
                "effect_match_name": "OLM RadialBlur", "plumbing_output_path": "/tmp/a.png",
                "type3": {"status": "live_type3_timeout", "pixel_exact": False},
                "scope": "load/add/render plumbing; Type3 non-exact"}
        RUNNER_MODULE.validate_result(base)
        base["type3"]["pixel_exact"] = True
        with self.assertRaisesRegex(ValueError, "pixel claim"): RUNNER_MODULE.validate_result(base)

if __name__ == "__main__": unittest.main()
