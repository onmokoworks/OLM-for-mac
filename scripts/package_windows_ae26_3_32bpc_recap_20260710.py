#!/usr/bin/env python3
"""Package the Windows AE 26.3 32bpc EXR recapture request."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


REQUESTS = (
    "olm_bitdepth_32bpc_full_probe_exr_rerun_20260703.json",
    "olm_bitdepth_32bpc_olmdirectionalblur_exr_20260710.json",
    "olm_bitdepth_32bpc_olmkirakira_exr_20260710.json",
    "olm_bitdepth_32bpc_olmradialblur_exr_20260710.json",
    "olm_bitdepth_32bpc_olmsmoother2_exr_20260710.json",
    "olm_bitdepth_32bpc_olmsmoother_v1_exr_20260710.json",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("refs/reference_requests/olm_windows_reference_request_ae26_3_32bpc_recap_20260710.zip"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output if args.output.is_absolute() else root / args.output
    base = root / "refs" / "reference_requests"
    payload = (
        base / "AE_26_3_32BPC_RECAPTURE_20260710.md",
        base / "README.md",
        base / "WIN_CODEX_HANDOFF.md",
        *(base / name for name in REQUESTS),
    )
    missing = [str(path) for path in payload if not path.is_file()]
    if missing:
        raise SystemExit("missing package input:\n" + "\n".join(missing))

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in payload:
            archive.write(path, path.relative_to(root).as_posix())
    print(f"[OK] Windows AE 26.3 32bpc recapture package: {output}")
    print("[SUMMARY] specs=6 cases=98 required_ae=26.3 renderer=SOFTWARE output=FLOAT_EXR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
