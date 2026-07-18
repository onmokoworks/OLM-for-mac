#!/usr/bin/env python3
"""RadialBlur-only natural worker progress hook.

This wrapper deliberately leaves the shared case0009 runner untouched.  It
adds one exact-address, read-only Unicorn hook to the natural worker, then
delegates the natural render/checkpoint work to
``test_zoom_case0009``.

The default ``cell`` mode observes immediately after the cell-completion
increment (0x18000b0b7).  ``row`` mode observes after the outer-row store
(0x18000b0f9) and is intended for low-overhead long-run progress.

The wrapper refuses all direct-core, synthetic-prefill, and worker-detour
options.  Progress is written to a sidecar JSON so a checkpoint/resume pair
can be inspected without changing the AEX state.
"""

from __future__ import annotations

import argparse
import atexit
import json
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import (
    UC_X86_REG_R12,
    UC_X86_REG_R14,
    UC_X86_REG_R15,
    UC_X86_REG_RSP,
)

sys.path.insert(0, str(Path(__file__).parent))
import test_zoom_case0009 as shared  # noqa: E402
from aex_loader import AexLoader  # noqa: E402


WORKER_CELL_COMPLETION_BEFORE_INCREMENT = 0x18000B0B4
WORKER_CELL_PROGRESS_AFTER_INCREMENT = 0x18000B0B7
WORKER_ROW_STORE = 0x18000B0F1
WORKER_ROW_PROGRESS_AFTER_STORE = 0x18000B0F9
DEFAULT_PROGRESS_JSON = Path("/tmp/olm_radialblur_natural_progress_20260718.json")
FORBIDDEN_OPTIONS = {
    "--direct-zoom-core",
    "--direct-debug-size",
    "--direct-debug-quality-step",
    "--direct-fast-forward-prefill",
    "--direct-python-prefill",
    "--direct-stop-after-prefill",
    "--direct-detour-prepass",
    "--direct-detour-scatter",
}


def parse_wrapper_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--progress-json", type=Path, default=DEFAULT_PROGRESS_JSON)
    parser.add_argument("--sample-every", type=int, default=8192)
    parser.add_argument("--max-samples", type=int, default=256)
    parser.add_argument(
        "--hook-mode",
        choices=("cell", "row"),
        default="cell",
        help=(
            "Observe every completed cell (cell) or only after the worker stores "
            "the next row index (row). Row mode is the low-overhead progress mode."
        ),
    )
    args, passthrough = parser.parse_known_args(argv)
    if args.sample_every <= 0:
        raise SystemExit("--sample-every must be positive")
    if args.max_samples <= 0:
        raise SystemExit("--max-samples must be positive")
    for option in FORBIDDEN_OPTIONS:
        if option in passthrough:
            raise SystemExit(f"refusing forbidden natural-run option: {option}")
    return args, passthrough


def read_progress(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema": 2,
            "hook": hex(WORKER_CELL_PROGRESS_AFTER_INCREMENT),
            "hook_phase": "after_inc_r14d_before_dec_r15d",
            "sample_every": None,
            "samples": [],
            "runs": [],
        }
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("schema") != 2:
        raise ValueError(
            f"unsupported RadialBlur progress schema {report.get('schema')!r}; "
            "use a fresh --progress-json path"
        )
    # A process may have been interrupted after a live sidecar write.  Those
    # samples are intentionally observational and must not be committed into
    # the next run's cumulative history.
    report.pop("live_run", None)
    return report


def write_progress(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    wrapper_args, passthrough = parse_wrapper_args(sys.argv[1:])
    progress = read_progress(wrapper_args.progress_json)
    progress["sample_every"] = wrapper_args.sample_every
    progress["schema"] = 2
    hook_address = (
        WORKER_CELL_PROGRESS_AFTER_INCREMENT
        if wrapper_args.hook_mode == "cell"
        else WORKER_ROW_PROGRESS_AFTER_STORE
    )
    progress["hook"] = hex(hook_address)
    progress["hook_mode"] = wrapper_args.hook_mode
    progress["hook_phase"] = (
        "after_inc_r14d_before_dec_r15d"
        if wrapper_args.hook_mode == "cell"
        else "after_row_store_before_row_loop_compare"
    )
    run_samples: list[dict[str, Any]] = []
    run_index = len(progress.get("runs", []))
    state: dict[str, Any] = {"hits": 0, "samples": run_samples, "installed_loader": None}

    original_add_code_hook = AexLoader.add_code_hook

    def write_live_progress() -> None:
        snapshot = dict(progress)
        committed_samples = list(progress.get("samples", []))
        visible_samples = [*committed_samples, *run_samples]
        snapshot["samples"] = committed_samples
        snapshot["live_run"] = {
            "run_index": run_index,
            "samples": run_samples,
            "boundary_hits": state["hits"],
            "passthrough": passthrough,
        }
        snapshot["total_samples"] = len(visible_samples)
        snapshot["total_boundary_hits"] = sum(
            int(run.get("boundary_hits", 0)) for run in progress.get("runs", [])
        ) + state["hits"]
        snapshot["monotonic_check"] = monotonic_check(visible_samples)
        write_progress(wrapper_args.progress_json, snapshot)

    def add_code_hook_with_radial_progress(loader: AexLoader, guest_addr: int, handler) -> None:
        original_add_code_hook(loader, guest_addr, handler)
        if state["installed_loader"] is not None:
            if state["installed_loader"] is not loader:
                raise RuntimeError("progress hook was attached to more than one AexLoader")
            return
        state["installed_loader"] = loader

        def capture_worker_boundary(ld: AexLoader, address: int, size: int) -> None:
            state["hits"] += 1
            hit = int(state["hits"])
            if hit % wrapper_args.sample_every:
                return
            if len(run_samples) >= wrapper_args.max_samples:
                return
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            row = shared.u32(ld, rsp + 0xC8)
            row_width = shared.u32(ld, rsp + 0xB8)
            worker_end_row = shared.u32(ld, rsp + 0xD0)
            cell = ld.uc.reg_read(UC_X86_REG_R14) & 0xFFFFFFFF
            row_reg = ld.uc.reg_read(UC_X86_REG_R12) & 0xFFFFFFFFFFFFFFFF
            row_end_reg = ld.uc.reg_read(UC_X86_REG_R15) & 0xFFFFFFFFFFFFFFFF
            run_samples.append(
                {
                    "hit": hit,
                    "run_index": run_index,
                    "address": hex(address),
                    "instruction_size": size,
                    "row_stack": row,
                    "cell_after_inc_r14d": cell,
                    "row_width_stack": row_width,
                    "worker_end_row_stack": worker_end_row,
                    "row_r12": row_reg,
                    "row_end_r15": row_end_reg,
                    "instructions_executed": ld.instructions_executed,
                    "hook_mode": wrapper_args.hook_mode,
                }
            )
            write_live_progress()

        original_add_code_hook(loader, hook_address, capture_worker_boundary)

    AexLoader.add_code_hook = add_code_hook_with_radial_progress

    previous_samples = len(progress.get("samples", []))

    def flush() -> None:
        progress.setdefault("runs", []).append(
            {
                "samples_added": len(run_samples),
                "boundary_hits": state["hits"],
                "hook_mode": wrapper_args.hook_mode,
                "passthrough": passthrough,
            }
        )
        progress["samples"] = [*progress.get("samples", []), *run_samples]
        progress["total_samples"] = len(progress["samples"])
        progress["total_boundary_hits"] = sum(
            int(run.get("boundary_hits", 0)) for run in progress["runs"]
        )
        progress["monotonic_check"] = monotonic_check(progress["samples"])
        progress.pop("live_run", None)
        write_progress(wrapper_args.progress_json, progress)
        print(f"radial_progress_json={wrapper_args.progress_json}")
        print(f"radial_boundary_hits={state['hits']}")
        print(f"radial_samples_added={len(run_samples)}")
        print(f"radial_samples_before_run={previous_samples}")
        print(f"radial_monotonic={progress['monotonic_check']}")

    atexit.register(flush)
    sys.argv = [sys.argv[0], *passthrough]
    try:
        return int(shared.main())
    finally:
        AexLoader.add_code_hook = original_add_code_hook


def monotonic_check(samples: list[dict[str, Any]]) -> bool:
    previous_by_run: dict[int, tuple[int, int, int]] = {}
    for sample in samples:
        run_index = int(sample.get("run_index", 0))
        current = (
            int(sample["row_stack"]),
            int(sample.get("cell_after_inc_r14d", sample.get("cell_r14d", 0))),
            int(sample["instructions_executed"]),
        )
        previous = previous_by_run.get(run_index)
        if previous is not None and current < previous:
            return False
        previous_by_run[run_index] = current
    return True


if __name__ == "__main__":
    raise SystemExit(main())
