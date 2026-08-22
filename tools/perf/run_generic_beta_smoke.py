#!/usr/bin/env python3
"""Run bounded hostless generic-beta smokes and emit a machine-readable report.

The command catalog is intentionally explicit. A lane/geometry without an exact
hostless driver is recorded as ``not_measured`` rather than being represented by
a smaller fixture. Commands may be added as generic lanes acquire scalable
drivers; this runner itself does not depend on the Adobe host.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
import platform
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
GEOMETRIES = {"hd": [1920, 1080], "uhd": [3840, 2160]}
LANES = [
    "ColorKeep", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur", "OLMSmoother",
    "OLMSmoother2", "OLMToonDilate",
]

# Only commands proven to execute the exact requested geometry belong here.
# Each driver uses safe/default parameters and is independently time-limited.
COMMANDS: dict[tuple[str, str], list[str]] = {
    ("ColorKeep", "hd"): [
        sys.executable, "tools/perf/run_colorkeep_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("ColorKeep", "uhd"): [
        sys.executable, "tools/perf/run_colorkeep_generic_production_perf.py",
        "--geometry", "uhd",
    ],
    ("OLMBlur", "hd"): [
        sys.executable, "tools/perf/run_olmblur_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("OLMBlur", "uhd"): [
        sys.executable, "tools/perf/run_olmblur_generic_production_perf.py",
        "--geometry", "uhd",
    ],
    ("OLMColorKey", "hd"): [
        sys.executable, "tests/test_olmcolorkey_generic_pixel_local_pairwise.py",
        "--geometry", "hd",
    ],
    ("OLMColorKey", "uhd"): [
        sys.executable, "tests/test_olmcolorkey_generic_pixel_local_pairwise.py",
        "--geometry", "uhd",
    ],
    ("OLMDirectionalBlur", "hd"): [
        sys.executable, "tools/emulation/test_dblur_generic_deep_geometry_beta_20260820.py",
        "--geometry", "hd",
    ],
    ("OLMDirectionalBlur", "uhd"): [
        sys.executable, "tools/emulation/test_dblur_generic_deep_geometry_beta_20260820.py",
        "--geometry", "uhd",
    ],
    ("OLMDistanceGradation", "hd"): [
        sys.executable, "-m", "unittest",
        "tests/test_olmdistancegradation_generic_production_beta_20260820.py",
    ],
    ("OLMDistanceGradation", "uhd"): [
        sys.executable, "-m", "unittest",
        "tests/test_olmdistancegradation_generic_production_beta_20260820.py",
    ],
    ("OLMKiraKira", "hd"): [
        sys.executable, "tools/perf/run_olmkirakira_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("OLMKiraKira", "uhd"): [
        sys.executable, "tools/perf/run_olmkirakira_generic_production_perf.py",
        "--geometry", "uhd",
    ],
    ("OLMRadialBlur", "hd"): [
        sys.executable, "tools/perf/run_olmradialblur_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("OLMRadialBlur", "uhd"): [
        sys.executable, "tools/perf/run_olmradialblur_generic_production_perf.py",
        "--geometry", "uhd",
    ],
    ("OLMSmoother", "hd"): [
        sys.executable, "tests/run_olmsmoother_v1_generic_production_perf.py",
        "--depth", "both", "--width", "1920", "--height", "1080",
        "--input-padding", "18", "--output-padding", "34",
        "--tolerance", "255", "--use-key",
    ],
    ("OLMSmoother", "uhd"): [
        sys.executable, "tests/run_olmsmoother_v1_generic_production_perf.py",
        "--depth", "both", "--width", "3840", "--height", "2160",
        "--input-padding", "18", "--output-padding", "34",
        "--tolerance", "255", "--use-key",
    ],
    ("OLMSmoother2", "hd"): [
        sys.executable, "-m", "unittest",
        "tests.test_olmsmoother2_default_beta_lane_20260820."
        "OLMSmoother2DefaultBetaLane."
        "test_effectmain_accepts_arbitrary_source_at_all_depths",
    ],
    ("OLMSmoother2", "uhd"): [
        sys.executable, "-m", "unittest",
        "tests.test_olmsmoother2_default_beta_lane_20260820."
        "OLMSmoother2DefaultBetaLane."
        "test_effectmain_accepts_arbitrary_source_at_all_depths",
    ],
    ("OLMToonDilate", "hd"): [
        sys.executable, "tools/perf/run_olmtoondilate_generic_production_perf.py",
        "--geometry", "hd",
    ],
    ("OLMToonDilate", "uhd"): [
        sys.executable, "tools/perf/run_olmtoondilate_generic_production_perf.py",
        "--geometry", "uhd",
    ],
}

# The files below are the in-repository inputs that directly select or compile
# each performance lane.  System SDK headers and the compiler installation are
# recorded in platform/tool metadata rather than pretending this is a complete
# compiler dependency graph.  Every lane binding also includes this runner.
LANE_DEPENDENCIES: dict[str, tuple[tuple[str, str], ...]] = {
    "ColorKeep": (
        ("driver", "tools/perf/run_colorkeep_generic_production_perf.py"),
        ("production_source", "mac/ColorKeep/ColorKeep.cpp"),
        ("production_header", "mac/ColorKeep/ColorKeep.h"),
        ("production_auxiliary", "mac/ColorKeep/ColorKeep_Strings.cpp"),
        ("production_header", "mac/ColorKeep/ColorKeep_Strings.h"),
    ),
    "OLMBlur": (
        ("driver", "tools/perf/run_olmblur_generic_production_perf.py"),
        ("driver_dependency", "tests/test_olmblur_generic_beta_sanitizers_20260820.py"),
        ("harness", "tools/emulation/probe_olmblur_generic_beta_sanitized_20260820.cpp"),
        ("production_source", "mac/OLMBlur/OLMBlur.cpp"),
        ("production_header", "mac/OLMBlur/OLMBlur.h"),
        ("production_auxiliary", "mac/OLMBlur/OLMBlur_Strings.cpp"),
        ("production_header", "mac/OLMBlur/OLMBlur_Strings.h"),
        ("production_auxiliary", "core/olmblur_helper.cpp"),
        ("production_header", "core/olmblur_helper.h"),
        ("production_auxiliary", "core/olmblur_fullworker_helper.cpp"),
        ("production_header", "core/olmblur_fullworker_helper.h"),
        ("production_auxiliary", "core/olmblur_worker16_nonlegacy.cpp"),
        ("production_header", "core/olmblur_worker16_nonlegacy.h"),
        ("production_auxiliary", "core/olmblur_worker16_legacy.cpp"),
        ("production_header", "core/olmblur_worker16_legacy.h"),
        ("production_auxiliary", "core/olmblur_worker32_nonlegacy.cpp"),
        ("production_header", "core/olmblur_worker32_nonlegacy.h"),
        ("production_auxiliary", "core/olmblur_worker32_legacy.cpp"),
        ("production_header", "core/olmblur_worker32_legacy.h"),
        ("production_auxiliary", "core/olmblur_worker8_legacy.cpp"),
        ("production_header", "core/olmblur_worker8_legacy.h"),
        ("production_auxiliary", "core/olmblur_worker_orchestration.cpp"),
        ("production_header", "core/olmblur_worker_orchestration.h"),
        ("production_header", "core/olm_world_safety.h"),
    ),
    "OLMColorKey": (
        ("driver", "tests/test_olmcolorkey_generic_pixel_local_pairwise.py"),
        ("harness", "tests/probe_olmcolorkey_generic_pixel_local_pairwise.cpp"),
        ("production_source", "mac/OLMColorKey/OLMColorKey.cpp"),
        ("production_header", "mac/OLMColorKey/OLMColorKey.h"),
        ("production_auxiliary", "mac/OLMColorKey/OLMColorKey_Strings.cpp"),
        ("production_header", "mac/OLMColorKey/OLMColorKey_Strings.h"),
    ),
    "OLMDirectionalBlur": (
        ("driver", "tools/emulation/test_dblur_generic_deep_geometry_beta_20260820.py"),
        ("production_source", "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"),
        ("production_header", "mac/OLMDirectionalBlur/OLMDirectionalBlur.h"),
        ("production_header", "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.h"),
        ("production_header", "core/dblur_generic_budget.h"),
        ("production_auxiliary", "core/dblur_frontonly.cpp"),
        ("production_auxiliary", "core/dblur_frontonly.h"),
        ("production_auxiliary", "core/dblur_rotate.cpp"),
        ("production_auxiliary", "core/dblur_rotate.h"),
        ("production_auxiliary", "core/dblur_rowdriver.cpp"),
        ("production_auxiliary", "core/dblur_rowdriver.h"),
        ("production_auxiliary", "core/dblur_field.cpp"),
        ("production_auxiliary", "core/dblur_field.h"),
        ("production_header", "core/dblur_gaussian.h"),
        ("production_header", "core/dblur_noise.h"),
        ("production_header", "core/olm_checked_allocation.h"),
        ("production_header", "core/olm_sha256_rows.h"),
    ),
    "OLMDistanceGradation": (
        ("driver", "tests/test_olmdistancegradation_generic_production_beta_20260820.py"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716_sdk_shim.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/AEConfig.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/AEFX_ChannelDepthTpl.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/AEFX_SuiteHelper.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/AEGP_SuiteHandler.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/AE_Effect.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/AE_EffectCB.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/AE_EffectCBSuites.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/AE_GeneralPlug.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/AE_Macros.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/Param_Utils.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/String_Utils.h"),
        ("harness", "tools/emulation/dg_renderbits_real_harness_20260716/entry.h"),
        ("production_source", "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"),
        ("production_header", "mac/OLMDistanceGradation/OLMDistanceGradation.h"),
        ("production_header", "mac/OLMDistanceGradation/OLMDistanceGradation_Strings.h"),
        ("production_auxiliary", "core/olmdistancegradation_fieldgen.cpp"),
        ("production_auxiliary", "core/olmdistancegradation_fieldgen.h"),
        ("production_header", "core/olm_world_safety.h"),
    ),
    "OLMKiraKira": (
        ("driver", "tools/perf/run_olmkirakira_generic_production_perf.py"),
        ("harness", "tests/olmkirakira_generic_beta_sanitizer_harness.cpp"),
        ("harness", "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"),
        ("production_source", "mac/OLMKiraKira/OLMKiraKira.cpp"),
        ("production_header", "mac/OLMKiraKira/OLMKiraKira.h"),
        ("production_auxiliary", "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"),
        ("production_header", "mac/OLMKiraKira/OLMKiraKira_Strings.h"),
        ("production_header", "core/kirakira_gaussian.h"),
        ("production_header", "core/kirakira_highlight.h"),
        ("production_header", "core/kirakira_mode4.h"),
        ("production_header", "core/kirakira_warp.h"),
        ("production_header", "core/kirakira_merge2.h"),
    ),
    "OLMRadialBlur": (
        ("driver", "tools/perf/run_olmradialblur_generic_production_perf.py"),
        ("production_source", "mac/OLMRadialBlur/OLMRadialBlur.cpp"),
        ("production_header", "mac/OLMRadialBlur/OLMRadialBlur.h"),
        ("production_header", "mac/OLMRadialBlur/OLMRadialBlur_Strings.h"),
        ("production_header", "core/dblur_noise.h"),
        ("production_header", "core/olm_sha256_rows.h"),
    ),
    "OLMSmoother": (
        ("driver", "tests/run_olmsmoother_v1_generic_production_perf.py"),
        ("harness", "tests/test_olmsmoother_v1_generic_classic_beta_20260820.py"),
        ("production_source", "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"),
        ("production_resource", "mac/OLMSmoother/OLMSmootherPiPL.r"),
        ("production_header", "core/olm_sha256_rows.h"),
        ("production_header", "core/olm_world_safety.h"),
        ("production_auxiliary", "mac/OLMSmoother/Mac/OLMSmoother_classifier8_tail.generated.inc"),
        ("production_auxiliary", "mac/OLMSmoother/Mac/OLMSmoother_classifier16.generated.inc"),
        ("production_auxiliary", "mac/OLMSmoother/Mac/OLMSmoother_edgewalker16.generated.inc"),
        ("production_auxiliary", "mac/OLMSmoother/Mac/OLMSmoother_subhandler16.generated.inc"),
        ("production_auxiliary", "mac/OLMSmoother/Mac/OLMSmoother_edgewalker8.generated.inc"),
        ("production_auxiliary", "mac/OLMSmoother/Mac/OLMSmoother_subhandler8.generated.inc"),
        ("build_dependency", "cli/OLMSmoother/shim/OLMSmoother.h"),
        ("build_dependency", "cli/OLMSmoother/shim/AEFX_SuiteHandlerTemplate.h"),
    ),
    "OLMSmoother2": (
        ("driver", "tests/test_olmsmoother2_default_beta_lane_20260820.py"),
        ("harness", "tools/emulation/olmsmoother2_public_guard_harness_20260812.cpp"),
        ("production_source", "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"),
        ("production_header", "core/olm_sha256_rows.h"),
        ("production_header", "mac/OLMSmoother2/Mac/OLMSmoother2_decode_lut_10000.h"),
        ("production_header", "mac/OLMSmoother2/Mac/OLMSmoother2_encode_lut_10000.h"),
        ("build_dependency", "cli/OLMSmoother2/shim/OLMSmoother2.h"),
    ),
    "OLMToonDilate": (
        ("driver", "tools/perf/run_olmtoondilate_generic_production_perf.py"),
        ("harness", "tests/test_olmtoondilate_generic_beta.py"),
        ("production_source", "mac/OLMToonDilate/OLMToonDilate.cpp"),
        ("conservative_suppressed_header", "mac/OLMToonDilate/OLMToonDilate.h"),
    ),
}
SUPPORT_PREDICATES = {
    "ColorKeep": (
        "smart && pf8_pf16_pf32 && full_frame && zero_origin && "
        "1 <= count <= 100 && width <= 3840 && height <= 2160"
    ),
    "OLMBlur": (
        "smart && pf8_pf16_pf32 && full_frame && width <= 4096 && "
        "height <= 2160 && amount <= 1000 && repeat <= 10 && "
        "pixels*ceil(amount)*repeat <= 3600000000"
    ),
    "OLMDirectionalBlur": (
        "full_frame && pf8_pf16_pf32 && neutral_single_or_dual_side && "
        "at_least_one(front_strength,back_strength) && "
        "-32768 <= angle <= 32767.9999847412109375 && 0 <= gain <= 10 && "
        "0 <= front_strength,back_strength <= 4000 && active_strength >= 1 && "
        "0 < pf8_scale_x_y <= 1 && "
        "scale_1_for_pf16_pf32 && pf16_sdr_0_32768 && pf32_finite_sdr_0_1 && "
        "max(width,height) <= 4096 && width*height <= 8847360 && "
        "per_render_plugin_owned_live_bytes_with_64MiB_reserve <= 3221225472 && "
        "edge_clamped_operation_units <= 350000000"
    ),
    "OLMDistanceGradation": (
        "classic_pf8_pf16_pf32_or_smart_pf8_pf16 || "
        "(smart_pf32 && full_frame && zero_origin && "
        "positive_aligned_disjoint_rowbytes && max(width,height) <= 4096 && "
        "width*height <= 8847360 && finite_sdr_0_1 && "
        "((blur_none && interpolation in {constant,linear,sphere}) || "
        "bounded_windows_oracle_profile))"
    ),
    "OLMKiraKira": (
        "classic_or_smart && pf8_pf16_pf32 && full_frame && zero_origin && "
        "independent_nonoverlapping_rowbytes && width >= 9 && height >= 7 && "
        "max(width,height) <= 4096 && width*height <= 8847360 && "
        "pf16_sdr_0_32768 && pf32_finite_sdr_0_1 && "
        "(oracle_tuple || (mode3_horizontal_only && 1 <= length <= 300 && "
        "rotation in {0,1} && per_render_plugin_owned_bytes <= 1073741824 && "
        "mode3_work_units <= 12000000000)) && mode_geometry_admitted"
    ),
    "OLMRadialBlur": (
        "classic_or_smart && pf8_pf16_pf32 && full_frame_normalized_overscan && "
        "positive_aligned_independent_rowbytes && max(width,height) <= 4096 && "
        "width*height <= 8847360 && pf16_sdr_0_32768 && pf32_finite_sdr_0_1 && "
        "(baseline || (neutral_outer_only && size_variation in {25,100} && "
        "noise_variation in {25,100} && procedural_noise_type in {1,2} && "
        "finite_alpha_general_4_connected_topology_including_image_edges)) && "
        "per_render_plugin_owned_bytes <= 1073741824 && work_units <= 350000000"
    ),
    "OLMSmoother": (
        "classic && (pf8 || pf16) && (key_off || key_on) && "
        "full_frame && positive_disjoint_rowbytes && max(width,height) <= 4096 && "
        "width*height <= 8847360"
    ),
    "OLMSmoother2": (
        "smart && pf8_pf16_pf32 && v1_v2 && smoothing_ui_ranges && "
        "key_off_on_invert && "
        "(gamma_none || gamma_all || gamma_colors_count_1_5) && "
        "full_frame && 16 <= width,height <= 8192"
    ),
    "OLMToonDilate": (
        "smart && pf8_pf16_pf32 && full_frame && zero_origin && "
        "0 <= search_radius <= 100 && positive_independent_rowbytes"
    ),
}

TIMEOUT_SECONDS = {"hd": 120, "uhd": 180}
RSS_BUDGET_BYTES = {"hd": 2 * 1024**3, "uhd": 3 * 1024**3}
_RSS = re.compile(r"^\s*(\d+)\s+maximum resident set size\s*$", re.MULTILINE)
_CASE_RESULTS = re.compile(r"^OLM_PERF_CASES_JSON=(.+)$", re.MULTILINE)
CASE_DEPTH_COUNTS: dict[tuple[str, str], dict[int, int]] = {
    ("ColorKeep", geometry): {8: 3, 16: 3, 32: 3} for geometry in GEOMETRIES
} | {
    ("OLMBlur", "hd"): {8: 3, 16: 2, 32: 2},
    ("OLMBlur", "uhd"): {8: 2, 16: 2, 32: 2},
} | {
    (lane, geometry): {8: count, 16: count, 32: count}
    for lane, count in (
        ("OLMDirectionalBlur", 3), ("OLMKiraKira", 5),
        ("OLMRadialBlur", 4), ("OLMToonDilate", 1),
    )
    for geometry in GEOMETRIES
}
RUNNER_RELATIVE_PATH = "tools/perf/run_generic_beta_smoke.py"
SCHEMA_VERSION = 2
TOOLCHAIN_TREE_MAX_FILES = 2048
TOOLCHAIN_TREE_MAX_TOTAL_BYTES = 256 * 1024 * 1024
TOOLCHAIN_TREE_MAX_FILE_BYTES = 64 * 1024 * 1024
TOOLCHAIN_TREE_TIMEOUT_SECONDS = 10.0


class EvidenceBindingError(RuntimeError):
    """The report cannot be bound to the declared repository inputs."""


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _json_sha256(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_record(role: str, relative_path: str, root: Path = ROOT) -> dict[str, object]:
    if not role or not relative_path or Path(relative_path).is_absolute():
        raise EvidenceBindingError(f"invalid dependency entry: {role!r} {relative_path!r}")
    root_resolved = root.resolve()
    candidate = root / relative_path
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise EvidenceBindingError(f"missing dependency: {relative_path}") from error
    try:
        resolved.relative_to(root_resolved)
    except ValueError as error:
        raise EvidenceBindingError(f"dependency escapes repository: {relative_path}") from error
    if not resolved.is_file():
        raise EvidenceBindingError(f"dependency is not a regular file: {relative_path}")
    before = resolved.stat()
    payload = resolved.read_bytes()
    after = resolved.stat()
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or len(payload) != after.st_size:
        raise EvidenceBindingError(f"dependency changed while hashing: {relative_path}")
    return {
        "role": role,
        "path": relative_path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
    }


def capture_file_bindings(
    entries: Sequence[tuple[str, str]], root: Path = ROOT,
) -> list[dict[str, object]]:
    normalized = list(entries)
    if len({(role, path) for role, path in normalized}) != len(normalized):
        raise EvidenceBindingError("duplicate dependency role/path entry")
    return [_file_record(role, path, root) for role, path in normalized]


def verify_file_bindings(
    entries: Sequence[tuple[str, str]], expected: object, root: Path = ROOT,
) -> None:
    if not isinstance(expected, list):
        raise EvidenceBindingError("dependency files must be a list")
    current = capture_file_bindings(entries, root)
    if current != expected:
        raise EvidenceBindingError("dependency identity mismatch")


def _lane_entries(lane: str) -> tuple[tuple[str, str], ...]:
    if lane not in LANE_DEPENDENCIES:
        raise EvidenceBindingError(f"no dependency catalog for lane: {lane}")
    entries = (("runner", RUNNER_RELATIVE_PATH), *LANE_DEPENDENCIES[lane])
    roles = [role for role, _ in entries]
    if roles.count("runner") != 1 or roles.count("driver") != 1:
        raise EvidenceBindingError(f"lane must have one runner and driver: {lane}")
    if "production_source" not in roles:
        raise EvidenceBindingError(f"lane has no production source binding: {lane}")
    return entries


def _lane_catalog_projection(lane: str) -> dict[str, object]:
    return {
        "lane": lane,
        "commands": {
            geometry: COMMANDS.get((lane, geometry)) for geometry in GEOMETRIES
        },
        "support_predicate": SUPPORT_PREDICATES.get(lane),
        "dependencies": [
            {"role": role, "path": path} for role, path in _lane_entries(lane)
        ],
    }


def capture_lane_binding(lane: str, root: Path = ROOT) -> dict[str, object]:
    files = capture_file_bindings(_lane_entries(lane), root)
    catalog = _lane_catalog_projection(lane)
    binding = {
        "lane": lane,
        "catalog_sha256": _json_sha256(catalog),
        "files": files,
        "scope": (
            "declared in-repository runner, driver, harness/direct build inputs, "
            "and production source; excludes system SDK/compiler transitive inputs"
        ),
    }
    binding["binding_sha256"] = _json_sha256(binding)
    return binding


def verify_lane_binding(
    lane: str, binding: object, root: Path = ROOT,
) -> None:
    if not isinstance(binding, dict) or binding.get("lane") != lane:
        raise EvidenceBindingError(f"invalid lane binding: {lane}")
    unsigned = {key: value for key, value in binding.items() if key != "binding_sha256"}
    if binding.get("binding_sha256") != _json_sha256(unsigned):
        raise EvidenceBindingError(f"lane binding digest mismatch: {lane}")
    if binding.get("catalog_sha256") != _json_sha256(_lane_catalog_projection(lane)):
        raise EvidenceBindingError(f"lane catalog changed: {lane}")
    verify_file_bindings(_lane_entries(lane), binding.get("files"), root)


def capture_bindings(lanes: Iterable[str], root: Path = ROOT) -> dict[str, object]:
    return {lane: capture_lane_binding(lane, root) for lane in lanes}


def verify_bindings(
    bindings: object, lanes: Iterable[str], root: Path = ROOT,
) -> None:
    expected_lanes = list(lanes)
    if not isinstance(bindings, dict) or set(bindings) != set(expected_lanes):
        raise EvidenceBindingError("dependency binding lane set mismatch")
    for lane in expected_lanes:
        verify_lane_binding(lane, bindings[lane], root)


def _binary_identity(path: Path) -> dict[str, object]:
    resolved = path.resolve(strict=True)
    payload = resolved.read_bytes()
    return {
        "resolved_path": str(resolved),
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def platform_metadata() -> dict[str, object]:
    python_identity = _binary_identity(Path(sys.executable))
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "mac_ver": platform.mac_ver()[0],
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_executable": str(Path(sys.executable).resolve()),
        "python_executable_size_bytes": python_identity["size_bytes"],
        "python_executable_sha256": python_identity["sha256"],
        "byteorder": sys.byteorder,
    }


def _tree_identity(path: Path) -> dict[str, object]:
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        return {"path": str(path), "status": "missing"}
    if not resolved.is_dir():
        return {"path": str(path), "resolved_path": str(resolved), "status": "not_directory"}
    dangerous_roots = {Path("/").resolve(), Path.home().resolve(), ROOT.resolve()}
    if resolved in dangerous_roots:
        raise EvidenceBindingError(f"refusing broad toolchain tree: {resolved}")
    records: list[dict[str, object]] = []
    total_bytes = 0
    started = time.monotonic()
    files: list[Path] = []
    for item in resolved.rglob("*"):
        if time.monotonic() - started > TOOLCHAIN_TREE_TIMEOUT_SECONDS:
            raise EvidenceBindingError(f"toolchain tree scan timed out: {resolved}")
        if not item.is_file():
            continue
        files.append(item)
        if len(files) > TOOLCHAIN_TREE_MAX_FILES:
            raise EvidenceBindingError(f"toolchain tree has too many files: {resolved}")
    for item in sorted(files, key=lambda value: value.as_posix()):
        if time.monotonic() - started > TOOLCHAIN_TREE_TIMEOUT_SECONDS:
            raise EvidenceBindingError(f"toolchain tree hash timed out: {resolved}")
        before = item.stat()
        if before.st_size > TOOLCHAIN_TREE_MAX_FILE_BYTES:
            raise EvidenceBindingError(f"toolchain file exceeds size cap: {item}")
        if total_bytes + before.st_size > TOOLCHAIN_TREE_MAX_TOTAL_BYTES:
            raise EvidenceBindingError(f"toolchain tree exceeds byte cap: {resolved}")
        payload = item.read_bytes()
        after = item.stat()
        if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
                or len(payload) != after.st_size):
            raise EvidenceBindingError(f"toolchain file changed while hashing: {item}")
        records.append({
            "path": item.relative_to(resolved).as_posix(),
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        })
        total_bytes += len(payload)
    return {
        "path": str(path),
        "resolved_path": str(resolved),
        "status": "captured",
        "file_count": len(records),
        "total_bytes": total_bytes,
        "tree_sha256": _json_sha256(records),
        "limits": {
            "max_files": TOOLCHAIN_TREE_MAX_FILES,
            "max_total_bytes": TOOLCHAIN_TREE_MAX_TOTAL_BYTES,
            "max_file_bytes": TOOLCHAIN_TREE_MAX_FILE_BYTES,
            "timeout_seconds": TOOLCHAIN_TREE_TIMEOUT_SECONDS,
        },
    }


def _command_version(command: str, arguments: Sequence[str]) -> dict[str, object]:
    executable = shutil.which(command)
    if executable is None:
        return {"command": command, "status": "missing"}
    result = run_process_group(
        [executable, *arguments], 5.0, cwd=ROOT, env=os.environ,
    )
    if not result["launched"]:
        return {
            "command": command, "resolved_path": str(Path(executable).resolve()),
            "status": "launch_failed", "error": result.get("launch_error"),
        }
    if result["timed_out"]:
        return {
            "command": command, "resolved_path": str(Path(executable).resolve()),
            "status": "timeout", "timeout_cleanup": result.get("timeout_cleanup"),
        }
    output = (str(result["stdout"]) or str(result["stderr"])).strip()
    return {
        "command": command,
        **_binary_identity(Path(executable)),
        "returncode": result["returncode"],
        "version_output": output[:4000],
    }


def toolchain_metadata() -> dict[str, object]:
    xcrun = shutil.which("xcrun")
    macos_sdk: dict[str, object]
    if xcrun is None:
        macos_sdk = {"status": "xcrun_missing"}
    else:
        result = run_process_group(
            [xcrun, "--show-sdk-path"], 5.0, cwd=ROOT, env=os.environ,
        )
        sdk_path = str(result.get("stdout", "")).strip()
        returncode = result.get("returncode")
        macos_sdk = {
            "status": "captured" if returncode == 0 and sdk_path else "unavailable",
            "path": sdk_path or None,
            "returncode": returncode,
            "timed_out": result.get("timed_out"),
        }
        if returncode == 0 and sdk_path:
            settings_candidates = [
                Path(sdk_path) / "SDKSettings.json",
                Path(sdk_path) / "SDKSettings.plist",
            ]
            for settings in settings_candidates:
                if settings.is_file():
                    payload = settings.read_bytes()
                    macos_sdk["settings_path"] = str(settings)
                    macos_sdk["settings_sha256"] = hashlib.sha256(payload).hexdigest()
                    break
    time_path = Path("/usr/bin/time")
    time_identity: dict[str, object] = {"path": str(time_path), "status": "missing"}
    if time_path.is_file():
        payload = time_path.read_bytes()
        time_identity = {
            "path": str(time_path), "status": "captured",
            "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
        }
    return {
        "hardcoded_clangxx": _command_version("clang++", ("--version",)),
        "configured_cxx": _command_version(
            os.environ.get("CXX", "clang++"), ("--version",)
        ),
        "macos_sdk": macos_sdk,
        "time_wrapper": time_identity,
        "adobe_after_effects_sdk_workspace_roots": {
            relative: _tree_identity(ROOT / relative)
            for relative in ("Headers", "Util", "Resources")
        },
        "scope": (
            "External compiler/macOS SDK identity plus aggregate content identities "
            "for the Adobe SDK workspace symlink roots used by hostless builds."
        ),
    }


def validate_toolchain_metadata(value: object) -> None:
    if not isinstance(value, dict):
        raise EvidenceBindingError("toolchain metadata is not an object")
    for key in ("hardcoded_clangxx", "configured_cxx"):
        compiler = value.get(key)
        if (not isinstance(compiler, dict) or compiler.get("returncode") != 0
                or not isinstance(compiler.get("sha256"), str)):
            raise EvidenceBindingError(f"incomplete compiler identity: {key}")
    macos_sdk = value.get("macos_sdk")
    if not isinstance(macos_sdk, dict) or macos_sdk.get("status") != "captured":
        raise EvidenceBindingError("macOS SDK identity is unavailable")
    time_wrapper = value.get("time_wrapper")
    if not isinstance(time_wrapper, dict) or time_wrapper.get("status") != "captured":
        raise EvidenceBindingError("/usr/bin/time identity is unavailable")
    roots = value.get("adobe_after_effects_sdk_workspace_roots")
    if not isinstance(roots, dict) or set(roots) != {"Headers", "Util", "Resources"}:
        raise EvidenceBindingError("Adobe SDK workspace root identity set is incomplete")
    if any(not isinstance(item, dict) or item.get("status") != "captured"
           or not isinstance(item.get("tree_sha256"), str) for item in roots.values()):
        raise EvidenceBindingError("Adobe SDK workspace content identity is unavailable")


def invocation_metadata(
    argv: Sequence[str], lanes: Sequence[str], geometries: Sequence[str], mode: str,
) -> dict[str, object]:
    return {
        "mode": mode,
        "argv": [str(Path(sys.executable).resolve()), str(Path(__file__).resolve()), *argv],
        "working_directory": str(ROOT.resolve()),
        "caller_working_directory": str(Path.cwd().resolve()),
        "selected_lanes": list(lanes),
        "selected_geometries": list(geometries),
    }


def atomic_write_json(path: Path, report: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temp = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp",
    )
    temp_path = Path(raw_temp)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


@contextlib.contextmanager
def report_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_root = Path(tempfile.gettempdir()) / "olm_generic_beta_perf_locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_name = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest() + ".lock"
    lock_path = lock_root / lock_name
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _tail(value: object, limit: int = 1000) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value)[-limit:]


def _group_exists(process_group_id: int) -> bool:
    if os.name != "posix":
        return False
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _cleanup_process_group(
    process: subprocess.Popen[str], grace_seconds: float = 1.0,
) -> dict[str, object]:
    signals_sent: list[str] = []
    group_present = os.name == "posix" and _group_exists(process.pid)
    if group_present or process.poll() is None:
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
            signals_sent.append("SIGTERM")
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        direct_alive = process.poll() is None
        group_present = os.name == "posix" and _group_exists(process.pid)
        if not direct_alive and not group_present:
            break
        time.sleep(0.01)
    direct_alive = process.poll() is None
    group_present = os.name == "posix" and _group_exists(process.pid)
    if direct_alive or group_present:
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            signals_sent.append("SIGKILL")
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    deadline = time.monotonic() + grace_seconds
    while os.name == "posix" and _group_exists(process.pid) and time.monotonic() < deadline:
        time.sleep(0.01)
    return {
        "signals_sent": signals_sent,
        "termination_returncode": process.returncode,
        "process_group_reaped": (
            process.poll() is not None
            and (os.name != "posix" or not _group_exists(process.pid))
        ),
    }


def run_process_group(
    command: Sequence[str], timeout_seconds: float,
    *, cwd: Path = ROOT, env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    try:
        process = subprocess.Popen(
            list(command), cwd=cwd, text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(env) if env else None,
            start_new_session=(os.name == "posix"),
        )
    except OSError as error:
        return {
            "launched": False,
            "timed_out": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(error),
            "launch_error": f"{type(error).__name__}: {error}",
        }
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as error:
        partial_stdout = _tail(error.stdout, 1_000_000)
        partial_stderr = _tail(error.stderr, 1_000_000)
        cleanup = _cleanup_process_group(process)
        pipes_drained = True
        try:
            final_stdout, final_stderr = process.communicate(timeout=1.0)
            stdout = final_stdout if final_stdout else partial_stdout
            stderr = final_stderr if final_stderr else partial_stderr
        except subprocess.TimeoutExpired:
            pipes_drained = False
            stdout, stderr = partial_stdout, partial_stderr
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
        return {
            "launched": True,
            "timed_out": True,
            "returncode": None,
            "stdout": stdout,
            "stderr": stderr,
            "process_group_id": process.pid if os.name == "posix" else None,
            "timeout_cleanup": cleanup,
            "pipes_drained": pipes_drained,
        }
    except BaseException:
        _cleanup_process_group(process)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        raise
    lingering_cleanup: dict[str, object] | None = None
    if os.name == "posix" and _group_exists(process.pid):
        lingering_cleanup = _cleanup_process_group(process)
    return {
        "launched": True,
        "timed_out": False,
        "returncode": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "process_group_id": process.pid if os.name == "posix" else None,
        "lingering_process_group": lingering_cleanup is not None,
        "lingering_cleanup": lingering_cleanup,
    }


def measure(command: list[str], geometry: str) -> dict[str, object]:
    timeout = TIMEOUT_SECONDS[geometry]
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="olm_perf_time_") as raw:
        metrics_path = Path(raw) / "outer_time.txt"
        wrapped = ["/usr/bin/time", "-lp", "-o", str(metrics_path), *command]
        run = run_process_group(
            wrapped, timeout, cwd=ROOT,
            env={**os.environ, "OLM_PERF_GEOMETRY": geometry},
        )
        metrics = metrics_path.read_text(encoding="utf-8") if metrics_path.is_file() else ""
    elapsed = time.monotonic() - started
    if not run["launched"]:
        return {
            "status": "launch_failed", "timeout_seconds": timeout,
            "wall_seconds": round(elapsed, 6),
            "stdout_tail": _tail(run.get("stdout")),
            "stderr_tail": _tail(run.get("stderr")),
            "launch_error": run.get("launch_error"),
        }
    if run["timed_out"]:
        return {
            "status": "timeout", "timeout_seconds": timeout,
            "wall_seconds": round(elapsed, 6),
            "stdout_tail": _tail(run.get("stdout")),
            "stderr_tail": _tail(run.get("stderr")),
            "timeout_cleanup": run.get("timeout_cleanup"),
        }
    if run.get("lingering_process_group"):
        return {
            "status": "lingering_process_group",
            "returncode": run.get("returncode"),
            "timeout_seconds": timeout,
            "wall_seconds": round(elapsed, 6),
            "stdout_tail": _tail(run.get("stdout")),
            "stderr_tail": _tail(run.get("stderr")),
            "lingering_cleanup": run.get("lingering_cleanup"),
        }
    stderr = str(run["stderr"])
    stdout = str(run["stdout"])
    matches = _RSS.findall(metrics)
    rss = int(matches[0]) if len(matches) == 1 else None
    status = "passed" if run["returncode"] == 0 else "failed"
    if status == "passed" and rss is None:
        status = "rss_unavailable"
    if status == "passed" and rss is not None and rss > RSS_BUDGET_BYTES[geometry]:
        status = "rss_budget_exceeded"
    result = {
        "status": status, "returncode": run["returncode"],
        "wall_seconds": round(elapsed, 6), "peak_rss_bytes": rss,
        "rss_budget_bytes": RSS_BUDGET_BYTES[geometry],
        "timeout_seconds": timeout,
        "stdout_tail": _tail(stdout), "stderr_tail": _tail(stderr),
        "time_metrics_tail": _tail(metrics),
    }
    case_match = _CASE_RESULTS.search(stdout)
    if case_match:
        try:
            parsed = json.loads(case_match.group(1))
            if not isinstance(parsed, list):
                raise ValueError("case results are not a list")
            result["case_results"] = parsed
        except (json.JSONDecodeError, ValueError) as error:
            result["status"] = "malformed_case_results"
            result["case_results_error"] = str(error)
    return result


def _policy() -> dict[str, object]:
    return {
        "exact_geometry_required": True,
        "timeouts_seconds": TIMEOUT_SECONDS,
        "rss_budgets_bytes": RSS_BUDGET_BYTES,
        "support_predicate_scope": (
            "declared admission context only; each performance workload is "
            "bounded and does not exhaust every parameter in that predicate"
        ),
        "verification_scope": (
            "machine/toolchain-bound evidence: interpreter and compiler paths, "
            "binary hashes, OS identity, and SDK tree identities must still match"
        ),
        "note": (
            "Peak RSS is /usr/bin/time maximum resident set size for the "
            "hostless driver process, parsed from a dedicated outer -o metrics file."
        ),
    }


def _parameters(lane: str, geometry: str) -> str:
    value = (
        "pixel_local_pairwise_no_edge_lab76_excluded"
        if lane == "OLMColorKey" else
        "key_on_arbitrary_color_tolerance_255"
        if lane == "OLMSmoother" else "safe_default"
    )
    overrides = {
        "OLMRadialBlur": (
            "generic_baseline_plus_size25_noise25_type1_outer4_"
            "zoom_rotation_all_depths_independent_strides"
        ),
        "OLMBlur": (
            "representative_pf8_pf16_pf32_nonlegacy_legacy_amount3_repeat1_"
            "plus_pf8_nonlegacy_amount500_repeat1_independent_strides"
            if geometry == "hd" else
            "budget_pf8_pf16_pf32_nonlegacy_legacy_amount1_repeat1_"
            "independent_strides"
        ),
        "ColorKeep": (
            "smart_typed_workers_all_depths_counts_1_13_100_"
            "independent_strides_production_O2"
        ),
        "OLMSmoother2": (
            "small_v1_v2_key_invert_gamma_none_all_smoothing_axes_plus_"
            + ("hd_depth_specific_representatives" if geometry == "hd"
               else "uhd_safe_default_all_depths")
            + "_independent_strides_asan_ubsan"
        ),
        "OLMToonDilate": (
            "production_O2_pf8_radius13_scale1_pf16_radius2.5_scale0.5_"
            "pf32_radius0.99_scale1_independent_strides_chebyshev_oracle"
        ),
        "OLMDistanceGradation": (
            "oracle_profile_linear_power_gaussian_sphere_median_bilateral_"
            "plus_unblurred_sphere_all_depths_independent_strides"
        ),
        "OLMDirectionalBlur": (
            "neutral_single_dual_front_back_angle37.25_gain0.75_strength2_"
            "pf8_pf16_pf32_odd_independent_strides"
        ),
        "OLMKiraKira": (
            "box_tuple0_approximated_gaussian_tuple3_gaussian_length50_"
            "exponential_tuple9_gaussian_horizontal_length300_rotation1_"
            "pf8_pf16_pf32_smart_two_classic_parity_determinism"
        ),
    }
    return overrides.get(lane, value)


def _base_row(lane: str, geometry: str) -> dict[str, object]:
    row: dict[str, object] = {
        "lane": lane,
        "geometry": geometry,
        "dimensions": GEOMETRIES[geometry],
        "parameters": _parameters(lane, geometry),
        "hostless": True,
        "timeout_seconds": TIMEOUT_SECONDS[geometry],
        "rss_budget_bytes": RSS_BUDGET_BYTES[geometry],
    }
    if lane in SUPPORT_PREDICATES:
        row["support_predicate"] = SUPPORT_PREDICATES[lane]
        row["support_predicate_role"] = \
            "declared_admission_context_not_exhaustive_performance_coverage"
    command = COMMANDS.get((lane, geometry))
    if command is not None:
        row["command"] = command
    return row


def _catalog_projection(
    lanes: Sequence[str], geometries: Sequence[str],
) -> dict[str, object]:
    return {
        "policy": _policy(),
        "cells": [
            {
                "lane": lane,
                "geometry": geometry,
                "dimensions": GEOMETRIES[geometry],
                "parameters": _parameters(lane, geometry),
                "command": COMMANDS.get((lane, geometry)),
                "support_predicate": SUPPORT_PREDICATES.get(lane),
                "support_predicate_role": (
                    "declared_admission_context_not_exhaustive_performance_coverage"
                    if lane in SUPPORT_PREDICATES else None
                ),
                "timeout_seconds": TIMEOUT_SECONDS[geometry],
                "rss_budget_bytes": RSS_BUDGET_BYTES[geometry],
            }
            for lane in lanes for geometry in geometries
        ],
    }


def _is_finite_number(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _validate_case_results(
    row: Mapping[str, object], lane: str, geometry: str,
) -> None:
    cases = row.get("case_results")
    expected_depths = CASE_DEPTH_COUNTS.get((lane, geometry))
    if expected_depths is None:
        if cases is not None:
            raise EvidenceBindingError(
                f"unexpected structured case claim for process-exit lane: {lane}/{geometry}"
            )
        return
    if not isinstance(cases, list) or len(cases) != sum(expected_depths.values()):
        raise EvidenceBindingError(f"structured case count mismatch: {lane}/{geometry}")
    observed_depths = {8: 0, 16: 0, 32: 0}
    observed_identities: list[tuple[object, ...]] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise EvidenceBindingError(f"case result is not an object: {lane}/{geometry}/{index}")
        if "status" in case and case["status"] != "passed":
            raise EvidenceBindingError(f"case result did not pass: {lane}/{geometry}/{index}")
        if "returncode" in case:
            returncode = case["returncode"]
            if isinstance(returncode, bool) or not isinstance(returncode, int) or returncode != 0:
                raise EvidenceBindingError(f"case return code is invalid: {lane}/{geometry}/{index}")
        if "dimensions" in case and case["dimensions"] != GEOMETRIES[geometry]:
            raise EvidenceBindingError(f"case dimension mismatch: {lane}/{geometry}/{index}")
        if "geometry" in case and case["geometry"] != geometry:
            raise EvidenceBindingError(f"case geometry mismatch: {lane}/{geometry}/{index}")
        if "width" in case and case["width"] != GEOMETRIES[geometry][0]:
            raise EvidenceBindingError(f"case width mismatch: {lane}/{geometry}/{index}")
        if "height" in case and case["height"] != GEOMETRIES[geometry][1]:
            raise EvidenceBindingError(f"case height mismatch: {lane}/{geometry}/{index}")
        for timing_key in ("wall_seconds", "milliseconds"):
            if timing_key in case and (
                not _is_finite_number(case[timing_key]) or case[timing_key] < 0
            ):
                raise EvidenceBindingError(f"case timing is invalid: {lane}/{geometry}/{index}")
        if "peak_rss_bytes" in case:
            rss = case["peak_rss_bytes"]
            if (isinstance(rss, bool) or not isinstance(rss, int) or rss < 0
                    or rss > RSS_BUDGET_BYTES[geometry]):
                raise EvidenceBindingError(f"case RSS is invalid: {lane}/{geometry}/{index}")
        if lane == "OLMKiraKira":
            required = {
                "returncode", "dimensions", "wall_seconds", "peak_rss_bytes",
                "workload", "classic_smart_parity", "deterministic",
                "independent_strides", "input_span_unchanged",
                "output_padding_unchanged", "output_active_changed",
            }
            if not required.issubset(case):
                raise EvidenceBindingError(
                    f"Kira case evidence is incomplete: {lane}/{geometry}/{index}"
                )
            if case["workload"] != (
                "Smart plus two Classic production renders with parity/determinism checks"
            ):
                raise EvidenceBindingError(
                    f"Kira workload identity mismatch: {lane}/{geometry}/{index}"
                )
            if case["wall_seconds"] <= 0:
                raise EvidenceBindingError(
                    f"Kira case timing is not positive: {lane}/{geometry}/{index}"
                )
            if case["peak_rss_bytes"] <= 0:
                raise EvidenceBindingError(
                    f"Kira case RSS is not positive: {lane}/{geometry}/{index}"
                )
        for safety_key in (
            "input_span_unchanged", "output_active_changed",
            "output_padding_unchanged", "independent_strides",
            "opposite_side_output_differs",
            "profile_outputs_pairwise_differ",
        ):
            if safety_key in case and case[safety_key] is not True:
                raise EvidenceBindingError(
                    f"case safety flag is false: {lane}/{geometry}/{index}/{safety_key}"
                )
        depth = case.get("depth", case.get("depth_bpc"))
        if isinstance(depth, bool) or depth not in observed_depths:
            raise EvidenceBindingError(f"case depth is invalid: {lane}/{geometry}/{index}")
        observed_depths[int(depth)] += 1
        if lane == "ColorKeep":
            observed_identities.append((case.get("case"), depth, case.get("count")))
        elif lane == "OLMBlur":
            observed_identities.append((case.get("case"), depth, case.get("legacy")))
        elif lane == "OLMDirectionalBlur":
            observed_identities.append((
                case.get("side"), depth, case.get("angle"),
                case.get("brightness_gain"), case.get("front_strength"),
                case.get("back_strength"), case.get("input_padding_bytes"),
                case.get("output_padding_bytes"),
                case.get("independent_strides"),
                case.get("opposite_side_output_differs"),
                case.get("profile_outputs_pairwise_differ"),
            ))
        elif lane == "OLMKiraKira":
            observed_identities.append((
                case.get("mode"), case.get("tuple"), depth,
                case.get("horizontal_length"),
                case.get("rotation_degrees"), case.get("classic_smart_parity"),
                case.get("deterministic"), case.get("independent_strides"),
                case.get("input_span_unchanged"),
                case.get("output_padding_unchanged"),
                case.get("output_active_changed"),
                case.get("content_bounds"), case.get("callback_shape"),
            ))
        elif lane == "OLMRadialBlur":
            observed_identities.append((case.get("family"), case.get("profile"), depth))
        elif lane == "OLMToonDilate":
            observed_identities.append((
                depth, case.get("radius"), case.get("comp_width"),
                case.get("oracle"), case.get("independent_strides"),
            ))
    if observed_depths != expected_depths:
        raise EvidenceBindingError(f"case depth coverage mismatch: {lane}/{geometry}")
    dimensions = GEOMETRIES[geometry]
    if lane == "ColorKeep":
        expected_identities = {
            (f"smart_pf{depth}_count{count}", depth, count)
            for depth in (8, 16, 32) for count in (1, 13, 100)
        }
    elif lane == "OLMBlur":
        prefix = geometry
        expected_identities = {
            (f"{prefix}_{suffix}", depth, legacy)
            for depth in (8, 16, 32)
            for suffix, legacy in (("nl", 0), ("l", 1))
        }
        if geometry == "hd":
            expected_identities.add(("hd_high", 8, 0))
    elif lane == "OLMDirectionalBlur":
        expected_identities = {
            (side, depth, 37.25, 0.75,
             0 if side == "back" else 2,
             0 if side == "front" else 2,
             5 if depth == 8 else 1,
             17 if depth == 8 else 3,
             True, True, True)
            for side in ("front", "back", "dual") for depth in (8, 16, 32)
        }
    elif lane == "OLMKiraKira":
        expected_identities = {
            (mode, tuple_name, depth, length, rotation,
             True, True, True, True, True, True, "full", "1/1/1/0")
            for mode, tuple_name, length, rotation in (
                ("box", "m1_h7_r0", 7, 0.0),
                ("approximated_gaussian", "m2_h7_ramp_r0", 7, 0.0),
                ("gaussian_length50", "m3_h50_r0", 50, 0.0),
                ("exponential", "m4_highlight_r3", 0, 0.0),
                ("gaussian_length300", "m3_ui_length", 300, 1.0),
            )
            for depth in (8, 16, 32)
        }
    elif lane == "OLMRadialBlur":
        expected_identities = {
            (family, profile, depth) for family in ("zoom", "rotation")
            for profile in ("baseline", "size_noise")
            for depth in (8, 16, 32)
        }
    else:
        expected_identities = {
            (8, 13.0, dimensions[0], "chebyshev_single_seed_full_words", True),
            (16, 2.5, dimensions[0] * 2, "chebyshev_single_seed_full_words", True),
            (32, 0.99, dimensions[0], "chebyshev_single_seed_full_words", True),
        }
    if len(observed_identities) != len(set(observed_identities)) \
            or set(observed_identities) != expected_identities:
        raise EvidenceBindingError(f"structured case identity mismatch: {lane}/{geometry}")


def _validate_rows_against_catalog(
    report: Mapping[str, object], lanes: Sequence[str], geometries: Sequence[str],
    *, allow_legacy_contract_metadata: bool = False,
) -> list[dict[str, object]]:
    rows = report.get("results")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise EvidenceBindingError("report results must be a list of objects")
    expected_cells = {(lane, geometry) for lane in lanes for geometry in geometries}
    observed: dict[tuple[object, object], dict[str, object]] = {}
    for row in rows:
        key = (row.get("lane"), row.get("geometry"))
        if key in observed:
            raise EvidenceBindingError(f"duplicate performance cell: {key}")
        observed[key] = row
    if set(observed) != expected_cells:
        raise EvidenceBindingError("performance cell set does not match current catalog")
    observed_policy = report.get("policy")
    if allow_legacy_contract_metadata and isinstance(observed_policy, dict):
        observed_policy = dict(observed_policy)
        observed_policy["note"] = _policy()["note"]
        for key in ("support_predicate_scope", "verification_scope"):
            observed_policy.setdefault(key, _policy()[key])
    if observed_policy != _policy():
        raise EvidenceBindingError("performance policy does not match current catalog")
    for lane, geometry in expected_cells:
        row = observed[(lane, geometry)]
        if row.get("dimensions") != GEOMETRIES[geometry]:
            raise EvidenceBindingError(f"dimension mismatch: {lane}/{geometry}")
        if row.get("command") != COMMANDS.get((lane, geometry)):
            raise EvidenceBindingError(f"command mismatch: {lane}/{geometry}")
        if row.get("hostless") is not True:
            raise EvidenceBindingError(f"non-hostless row: {lane}/{geometry}")
        if (not allow_legacy_contract_metadata
                and row.get("parameters") != _parameters(lane, geometry)):
            raise EvidenceBindingError(f"parameter workload mismatch: {lane}/{geometry}")
        predicate = SUPPORT_PREDICATES.get(lane)
        if row.get("support_predicate") != predicate:
            raise EvidenceBindingError(f"support predicate mismatch: {lane}/{geometry}")
        expected_role = (
            "declared_admission_context_not_exhaustive_performance_coverage"
            if lane in SUPPORT_PREDICATES else None
        )
        observed_role = row.get("support_predicate_role")
        if (not allow_legacy_contract_metadata or observed_role is not None) \
                and observed_role != expected_role:
            raise EvidenceBindingError(f"support predicate role mismatch: {lane}/{geometry}")
        status = row.get("status")
        allowed_statuses = {
            "passed", "failed", "timeout", "launch_failed", "rss_unavailable",
            "rss_budget_exceeded", "malformed_case_results",
            "lingering_process_group", "dependency_mismatch", "dependency_changed",
            "invalid_evidence", "not_measured", "unsupported",
        }
        if not isinstance(status, str) or status not in allowed_statuses:
            raise EvidenceBindingError(f"missing row status: {lane}/{geometry}")
        command = COMMANDS.get((lane, geometry))
        if command is None and status not in {"not_measured", "unsupported"}:
            raise EvidenceBindingError(f"driverless cell has measured status: {lane}/{geometry}")
        if command is not None and status == "not_measured":
            raise EvidenceBindingError(f"catalogued driver was not measured: {lane}/{geometry}")
        if status == "passed":
            returncode = row.get("returncode")
            if isinstance(returncode, bool) or not isinstance(returncode, int) or returncode != 0:
                raise EvidenceBindingError(f"passed row has nonzero return code: {lane}/{geometry}")
            rss = row.get("peak_rss_bytes")
            wall = row.get("wall_seconds")
            if (isinstance(rss, bool) or not isinstance(rss, int)
                    or rss < 0 or rss > RSS_BUDGET_BYTES[geometry]):
                raise EvidenceBindingError(f"passed row has invalid RSS: {lane}/{geometry}")
            if (not _is_finite_number(wall) or wall < 0
                    or wall > TIMEOUT_SECONDS[geometry]):
                raise EvidenceBindingError(f"passed row has invalid wall time: {lane}/{geometry}")
            _validate_case_results(row, lane, geometry)
        if row.get("timeout_seconds") != TIMEOUT_SECONDS[geometry]:
            raise EvidenceBindingError(f"timeout mismatch: {lane}/{geometry}")
        if row.get("rss_budget_bytes") != RSS_BUDGET_BYTES[geometry]:
            raise EvidenceBindingError(f"RSS budget mismatch: {lane}/{geometry}")
    return rows


def _outcome(rows: Sequence[Mapping[str, object]]) -> tuple[str, str, int]:
    statuses = [row.get("status") for row in rows]
    if statuses and all(status == "passed" for status in statuses):
        return "COMPLETED", "PASS", 0
    if any(status not in {"passed", "not_measured", "unsupported"}
           for status in statuses):
        return "FAILED", "FAIL", 1
    if statuses:
        return "INCOMPLETE", "INCOMPLETE", 1
    return "INCOMPLETE", "INCOMPLETE", 1


def bind_existing_report(
    report: Mapping[str, object], *, source_report_sha256: str,
    argv: Sequence[str] = (), root: Path = ROOT,
) -> dict[str, object]:
    selector = report.get("invocation") or report.get("binding_invocation")
    if isinstance(selector, dict):
        selected_lanes = selector.get("selected_lanes")
        selected_geometries = selector.get("selected_geometries")
    else:
        selected_lanes = selected_geometries = None
    lanes = (list(selected_lanes) if isinstance(selected_lanes, list)
             and selected_lanes and all(lane in LANES for lane in selected_lanes)
             else list(LANES))
    geometries = (list(selected_geometries) if isinstance(selected_geometries, list)
                  and selected_geometries
                  and all(geometry in GEOMETRIES for geometry in selected_geometries)
                  else list(GEOMETRIES))
    rows = _validate_rows_against_catalog(
        report, lanes, geometries, allow_legacy_contract_metadata=True,
    )
    bindings = capture_bindings(lanes, root)
    verify_bindings(bindings, lanes, root)
    binding_toolchain = toolchain_metadata()
    validate_toolchain_metadata(binding_toolchain)
    binding_invocation = invocation_metadata(argv, lanes, geometries, "bind-existing")
    binding_platform = platform_metadata()
    bound = json.loads(json.dumps(report))
    measurement_run_id = report.get("run_id")
    for execution_key in ("invocation", "platform", "toolchain"):
        bound.pop(execution_key, None)
    prior_provenance = report.get("provenance")
    original_measurement_sha = source_report_sha256
    original_schema = report.get("schema_version")
    if isinstance(prior_provenance, dict):
        original_measurement_sha = str(
            prior_provenance.get("measurement_report_sha256", source_report_sha256)
        )
        original_schema = prior_provenance.get("measurement_schema_version", original_schema)
        measurement_run_id = prior_provenance.get("measurement_run_id", measurement_run_id)
    if original_schema == 1:
        measurement_run_id = None
    for row in bound["results"]:
        lane = row["lane"]
        geometry = row["geometry"]
        row["parameters"] = _parameters(lane, geometry)
        row["dependency_binding_sha256"] = bindings[lane]["binding_sha256"]
        if lane in SUPPORT_PREDICATES:
            row["support_predicate_role"] = \
                "declared_admission_context_not_exhaustive_performance_coverage"
    run_state, outcome, _ = _outcome(rows)
    bound.update({
        "schema_version": SCHEMA_VERSION,
        "policy": _policy(),
        "run_id": f"retrospective-{uuid.uuid4()}",
        "run_state": run_state,
        "outcome": outcome,
        "binding_at": _utc_now(),
        "binding_invocation": binding_invocation,
        "binding_platform": binding_platform,
        "binding_toolchain": binding_toolchain,
        "provenance": {
            "binding_mode": "retrospective_catalog_compatibility",
            "measurement_source_identity": "unproven",
            "does_not_prove_execution_against_bound_sources": True,
            "measurement_report_sha256": original_measurement_sha,
            "measurement_schema_version": original_schema,
            "measurement_run_id": measurement_run_id,
            "latest_input_report_sha256": source_report_sha256,
            "catalog_projection_sha256": _json_sha256(
                _catalog_projection(lanes, geometries)
            ),
            "dependency_bindings_sha256": _json_sha256(bindings),
            "dependency_bindings": bindings,
            "toolchain_sha256": _json_sha256(binding_toolchain),
            "invocation_sha256": _json_sha256(binding_invocation),
            "platform_sha256": _json_sha256(binding_platform),
            "results_sha256": _json_sha256(bound["results"]),
            "note": (
                "Current dependency hashes prove catalog compatibility at binding "
                "time only. "
                + ("Schema-1 measurements did not record a pre-run snapshot."
                   if original_schema == 1 else
                   "This retrospective copy does not carry forward execution-time proof.")
            ),
            "retrospective_transformations": [
                "preserved measurement values and case results",
                "added current dependency references and non-exhaustive predicate scope",
                "normalized workload labels to the current command catalog",
            ],
        },
    })
    return bound


def verify_report_bindings(report: Mapping[str, object], root: Path = ROOT) -> None:
    if report.get("schema_version") != SCHEMA_VERSION:
        raise EvidenceBindingError("report is not provenance schema version 2")
    invocation = report.get("invocation") or report.get("binding_invocation")
    if not isinstance(invocation, dict):
        raise EvidenceBindingError("report has no invocation metadata")
    invocation_argv = invocation.get("argv")
    if (not isinstance(invocation_argv, list) or len(invocation_argv) < 2
            or invocation_argv[0] != str(Path(sys.executable).resolve())
            or invocation_argv[1] != str(Path(__file__).resolve())):
        raise EvidenceBindingError("invocation executable prefix mismatch")
    if invocation.get("working_directory") != str(ROOT.resolve()):
        raise EvidenceBindingError("effective working directory mismatch")
    platform_info = report.get("platform") or report.get("binding_platform")
    if not isinstance(platform_info, dict):
        raise EvidenceBindingError("report has no platform metadata")
    toolchain = report.get("toolchain") or report.get("binding_toolchain")
    if not isinstance(toolchain, dict):
        raise EvidenceBindingError("report has no toolchain metadata")
    validate_toolchain_metadata(toolchain)
    lanes = invocation.get("selected_lanes")
    geometries = invocation.get("selected_geometries")
    if not isinstance(lanes, list) or not lanes or not all(lane in LANES for lane in lanes):
        raise EvidenceBindingError("invalid selected lane metadata")
    if (not isinstance(geometries, list) or not geometries
            or not all(geometry in GEOMETRIES for geometry in geometries)):
        raise EvidenceBindingError("invalid selected geometry metadata")
    rows = _validate_rows_against_catalog(report, lanes, geometries)
    provenance = report.get("provenance")
    if not isinstance(provenance, dict):
        raise EvidenceBindingError("report has no provenance object")
    if provenance.get("invocation_sha256") != _json_sha256(invocation):
        raise EvidenceBindingError("invocation metadata digest mismatch")
    if provenance.get("platform_sha256") != _json_sha256(platform_info):
        raise EvidenceBindingError("platform metadata digest mismatch")
    if platform_info != platform_metadata():
        raise EvidenceBindingError("current platform identity mismatch")
    if provenance.get("results_sha256") != _json_sha256(rows):
        raise EvidenceBindingError("results digest mismatch")
    bindings = provenance.get("dependency_bindings")
    if provenance.get("dependency_bindings_sha256") != _json_sha256(bindings):
        raise EvidenceBindingError("aggregate dependency binding digest mismatch")
    if provenance.get("catalog_projection_sha256") != _json_sha256(
        _catalog_projection(lanes, geometries)
    ):
        raise EvidenceBindingError("catalog projection digest mismatch")
    if provenance.get("toolchain_sha256") != _json_sha256(toolchain):
        raise EvidenceBindingError("toolchain digest mismatch")
    if toolchain != toolchain_metadata():
        raise EvidenceBindingError("current toolchain identity mismatch")
    verify_bindings(bindings, lanes, root)
    for row in rows:
        lane = str(row["lane"])
        if row.get("dependency_binding_sha256") != bindings[lane]["binding_sha256"]:
            raise EvidenceBindingError(f"row dependency reference mismatch: {lane}")
    expected_state, expected_outcome, _ = _outcome(rows)
    if (report.get("run_state") != expected_state
            or report.get("outcome") != expected_outcome):
        raise EvidenceBindingError("report outcome does not match row results")
    mode = provenance.get("binding_mode")
    if mode == "execution_pre_and_post":
        if invocation.get("mode") != "measure":
            raise EvidenceBindingError("execution report invocation mode mismatch")
        if (provenance.get("measurement_source_identity") != "exact_pre_and_post_match"
                or provenance.get("post_run_dependency_match") is not True
                or provenance.get("post_run_toolchain_match") is not True):
            raise EvidenceBindingError("execution-time dependency identity is incomplete")
    elif mode == "retrospective_catalog_compatibility":
        if invocation.get("mode") != "bind-existing":
            raise EvidenceBindingError("retrospective report invocation mode mismatch")
        if (provenance.get("measurement_source_identity") != "unproven"
                or provenance.get("does_not_prove_execution_against_bound_sources") is not True):
            raise EvidenceBindingError("retrospective scope is overstated")
    else:
        raise EvidenceBindingError(f"unknown provenance binding mode: {mode}")


def _running_report(
    run_id: str, started_at: str, argv: Sequence[str], lanes: Sequence[str],
    geometries: Sequence[str], platform_info: Mapping[str, object],
    toolchain: Mapping[str, object],
    bindings: Mapping[str, object] | None = None,
) -> dict[str, object]:
    invocation = invocation_metadata(argv, lanes, geometries, "measure")
    provenance: dict[str, object] = {
        "binding_mode": "execution_pre_and_post",
        "measurement_source_identity": "preflight_pending",
        "post_run_dependency_match": False,
        "post_run_toolchain_match": False,
        "toolchain_sha256": _json_sha256(toolchain),
        "invocation_sha256": _json_sha256(invocation),
        "platform_sha256": _json_sha256(platform_info),
    }
    if bindings is not None:
        provenance.update({
            "measurement_source_identity": "pre_run_snapshot_captured",
            "dependency_bindings_sha256": _json_sha256(bindings),
            "dependency_bindings": bindings,
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "run_state": "RUNNING",
        "outcome": None,
        "started_at": started_at,
        "generated_at_epoch_seconds": int(time.time()),
        "policy": _policy(),
        "invocation": invocation,
        "platform": platform_info,
        "toolchain": toolchain,
        "provenance": provenance,
        "results": [],
    }


def run_measurements(
    output: Path, lanes: Sequence[str], geometries: Sequence[str], argv: Sequence[str],
) -> int:
    run_id = str(uuid.uuid4())
    started_at = _utc_now()
    running: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "run_state": "RUNNING",
        "outcome": None,
        "started_at": started_at,
        "generated_at_epoch_seconds": int(time.time()),
        "policy": _policy(),
        "invocation": invocation_metadata(argv, lanes, geometries, "measure"),
        "provenance": {
            "binding_mode": "execution_pre_and_post",
            "measurement_source_identity": "preflight_pending",
            "post_run_dependency_match": False,
            "post_run_toolchain_match": False,
        },
        "results": [],
    }
    atomic_write_json(output, running)
    try:
        platform_info = platform_metadata()
        pre_toolchain = toolchain_metadata()
        validate_toolchain_metadata(pre_toolchain)
    except Exception as error:
        failed = dict(running)
        failed.update({
            "run_state": "FAILED", "outcome": "FAIL", "finished_at": _utc_now(),
            "preflight_error": f"toolchain capture failed: {type(error).__name__}: {error}",
        })
        atomic_write_json(output, failed)
        print(f"toolchain preflight failed: {error}", file=sys.stderr)
        return 1
    running = _running_report(
        run_id, started_at, argv, lanes, geometries, platform_info, pre_toolchain,
    )
    atomic_write_json(output, running)
    try:
        bindings = capture_bindings(lanes)
        verify_bindings(bindings, lanes)
    except EvidenceBindingError as error:
        failed = dict(running)
        failed.update({
            "run_state": "FAILED",
            "outcome": "FAIL",
            "finished_at": _utc_now(),
            "preflight_error": str(error),
        })
        atomic_write_json(output, failed)
        print(f"dependency preflight failed: {error}", file=sys.stderr)
        return 1
    running = _running_report(
        run_id, started_at, argv, lanes, geometries, platform_info, pre_toolchain,
        bindings,
    )
    atomic_write_json(output, running)
    rows: list[dict[str, object]] = []
    for lane in lanes:
        for geometry in geometries:
            base = _base_row(lane, geometry)
            base["dependency_binding_sha256"] = bindings[lane]["binding_sha256"]
            command = COMMANDS.get((lane, geometry))
            if command is None:
                base.update({
                    "status": "not_measured",
                    "reason": "no exact-geometry hostless driver is available",
                    "timeout_seconds": TIMEOUT_SECONDS[geometry],
                    "rss_budget_bytes": RSS_BUDGET_BYTES[geometry],
                })
            else:
                try:
                    verify_lane_binding(lane, bindings[lane])
                except EvidenceBindingError as error:
                    base.update({
                        "status": "dependency_mismatch",
                        "reason": str(error),
                        "timeout_seconds": TIMEOUT_SECONDS[geometry],
                        "rss_budget_bytes": RSS_BUDGET_BYTES[geometry],
                    })
                else:
                    base.update(measure(command, geometry))
                    try:
                        verify_lane_binding(lane, bindings[lane])
                    except EvidenceBindingError as error:
                        base.update({
                            "status": "dependency_changed",
                            "reason": str(error),
                        })
                    if base.get("status") == "passed":
                        try:
                            _validate_case_results(base, lane, geometry)
                        except EvidenceBindingError as error:
                            base.update({
                                "status": "invalid_evidence",
                                "reason": str(error),
                            })
            rows.append(base)
    post_dependency_match = True
    post_run_error: str | None = None
    try:
        verify_bindings(bindings, lanes)
    except EvidenceBindingError as error:
        post_dependency_match = False
        post_run_error = str(error)
    try:
        post_toolchain = toolchain_metadata()
        validate_toolchain_metadata(post_toolchain)
        post_toolchain_match = post_toolchain == pre_toolchain
    except Exception as error:
        post_toolchain_match = False
        post_run_error = f"post-run toolchain capture failed: {type(error).__name__}: {error}"
    if not post_toolchain_match and post_run_error is None:
        post_run_error = "toolchain identity changed during measurement"
    evidence_match = post_dependency_match and post_toolchain_match
    if not evidence_match:
        for row in rows:
            if row.get("status") == "passed":
                row["status"] = "dependency_changed"
                row["reason"] = post_run_error
    run_state, outcome, exit_code = _outcome(rows)
    final = dict(running)
    final.update({
        "run_state": run_state,
        "outcome": outcome,
        "finished_at": _utc_now(),
        "results": rows,
    })
    final["provenance"] = {
        "binding_mode": "execution_pre_and_post",
        "measurement_source_identity": (
            "exact_pre_and_post_match" if evidence_match else "dependency_changed"
        ),
        "post_run_dependency_match": post_dependency_match,
        "post_run_toolchain_match": post_toolchain_match,
        "post_run_error": post_run_error,
        "catalog_projection_sha256": _json_sha256(
            _catalog_projection(list(lanes), list(geometries))
        ),
        "dependency_bindings_sha256": _json_sha256(bindings),
        "dependency_bindings": bindings,
        "toolchain_sha256": _json_sha256(pre_toolchain),
        "invocation_sha256": _json_sha256(final["invocation"]),
        "platform_sha256": _json_sha256(platform_info),
        "results_sha256": _json_sha256(rows),
    }
    try:
        verify_report_bindings(final)
    except EvidenceBindingError as error:
        for row in rows:
            if row.get("status") == "passed":
                row["status"] = "invalid_evidence"
                row["reason"] = f"final report validation failed: {error}"
        run_state, outcome, exit_code = _outcome(rows)
        final.update({"run_state": run_state, "outcome": outcome, "results": rows})
        final["provenance"]["results_sha256"] = _json_sha256(rows)
        final["final_validation_error"] = str(error)
        try:
            verify_report_bindings(final)
        except EvidenceBindingError:
            # Still publish a complete, explicitly failed JSON rather than an
            # invalid PASS. The prior atomic RUNNING record was never stale.
            exit_code = 1
    atomic_write_json(output, final)
    measured = [row for row in rows
                if row["status"] not in {"not_measured", "unsupported"}]
    failed_rows = [row for row in measured if row["status"] != "passed"]
    print(
        f"wrote {output}: measured={len(measured)} "
        f"unavailable={len(rows)-len(measured)} failed={len(failed_rows)}"
    )
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "reports/generic_beta_perf_smoke.json")
    parser.add_argument("--lane", choices=LANES,
                        help="measure only this lane (all lanes by default)")
    parser.add_argument("--geometry", choices=GEOMETRIES,
                        help="measure only this geometry (both by default)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--bind-existing", type=Path,
                      help="bind an existing report to the current catalog without rerunning")
    mode.add_argument("--verify-only", type=Path,
                      help="verify an existing schema-v2 report against current files")
    args = parser.parse_args(argv_list)
    selected_lanes = [args.lane] if args.lane else list(LANES)
    selected_geometries = [args.geometry] if args.geometry else list(GEOMETRIES)
    if (args.bind_existing or args.verify_only) and (args.lane or args.geometry):
        parser.error("--lane/--geometry cannot be combined with report binding modes")
    if args.verify_only:
        try:
            report = json.loads(args.verify_only.read_text(encoding="utf-8"))
            verify_report_bindings(report)
        except (OSError, json.JSONDecodeError, EvidenceBindingError) as error:
            print(f"report verification failed: {error}", file=sys.stderr)
            return 1
        print(f"verified {args.verify_only}")
        return 0
    with report_lock(args.output):
        if args.bind_existing:
            try:
                source_bytes = args.bind_existing.read_bytes()
                source = json.loads(source_bytes)
                bound = bind_existing_report(
                    source,
                    source_report_sha256=hashlib.sha256(source_bytes).hexdigest(),
                    argv=argv_list,
                )
                verify_report_bindings(bound)
                atomic_write_json(args.output, bound)
            except (OSError, json.JSONDecodeError, EvidenceBindingError) as error:
                print(f"report binding failed: {error}", file=sys.stderr)
                return 1
            print(f"bound {args.bind_existing} -> {args.output}: {len(bound['results'])} cells")
            return 0
        return run_measurements(
            args.output, selected_lanes, selected_geometries, argv_list,
        )


if __name__ == "__main__":
    raise SystemExit(main())
